-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 24-11-2026 a las 22:54:41
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `automall`
--

DELIMITER $$
--
-- Procedimientos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_actualizar_cuotas_vencidas` ()   BEGIN
    UPDATE cuotas
    SET estado = 'Vencida'
    WHERE estado IN ('Pendiente', 'Parcial')
      AND monto_pagado < monto_cuota
      AND fecha_vencimiento < CURDATE();
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_agendar_cita` (IN `p_fecha` DATE, IN `p_hora` TIME, IN `p_cod_catalogo` INT, IN `p_cedula_usuario` VARCHAR(20), OUT `p_resultado` VARCHAR(100))   BEGIN
    DECLARE total_concurrentes INT DEFAULT 0;
    
    SELECT COUNT(*) INTO total_concurrentes 
    FROM automall.citas 
    WHERE fecha = p_fecha AND hora = p_hora AND activo = 1;
    
    IF total_concurrentes >= 3 THEN
        SET p_resultado = 'ERROR: El horario seleccionado ya cuenta con el máximo de citas simultáneas.';
    ELSE
        INSERT INTO automall.citas (estado, fecha, hora, cod_catalogo, cedula_usuario, activo)
        VALUES ('Pendiente', p_fecha, p_hora, p_cod_catalogo, p_cedula_usuario, 1);
        SET p_resultado = 'OK: Cita agendada exitosamente.';
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_aplicar_pago_a_cuotas` (IN `p_cod_pagos` INT, IN `p_cod_cuentas` INT, IN `p_monto_abonado` DECIMAL(15,2), IN `p_cod_cuota` INT)   BEGIN
    DECLARE v_restante DECIMAL(15,2);
    DECLARE v_cuota_id INT;
    DECLARE v_monto_cuota DECIMAL(15,2);
    DECLARE v_monto_pagado DECIMAL(15,2);
    DECLARE v_saldo_cuota DECIMAL(15,2);
    DECLARE v_aplicar DECIMAL(15,2);
    DECLARE v_nuevo_pagado DECIMAL(15,2);
    DECLARE v_total_pagado_cuenta DECIMAL(15,2);
    DECLARE v_deuda_total DECIMAL(15,2);
    DECLARE v_nueva_deuda DECIMAL(15,2);
    DECLARE v_done INT DEFAULT 0;

    DECLARE cur_cuotas CURSOR FOR
        SELECT cod_cuota, monto_cuota, monto_pagado
        FROM cuotas
        WHERE cod_cuentas = p_cod_cuentas
          AND estado IN ('Pendiente', 'Parcial', 'Vencida')
          AND (p_cod_cuota IS NULL OR p_cod_cuota = 0 OR cod_cuota >= p_cod_cuota)
        ORDER BY
          CASE WHEN p_cod_cuota IS NOT NULL AND cod_cuota = p_cod_cuota THEN 0 ELSE 1 END,
          numero_cuota ASC;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    SET v_restante = IFNULL(p_monto_abonado, 0.00);

    IF v_restante > 0 THEN
        OPEN cur_cuotas;

        leer_cuotas: LOOP
            FETCH cur_cuotas INTO v_cuota_id, v_monto_cuota, v_monto_pagado;
            IF v_done = 1 OR v_restante <= 0 THEN
                LEAVE leer_cuotas;
            END IF;

            SET v_saldo_cuota = GREATEST(0.00, v_monto_cuota - v_monto_pagado);

            IF v_saldo_cuota > 0 THEN
                SET v_aplicar = LEAST(v_restante, v_saldo_cuota);
                SET v_nuevo_pagado = v_monto_pagado + v_aplicar;

                INSERT INTO pago_cuota_detalle (cod_pagos, cod_cuota, monto_aplicado)
                VALUES (p_cod_pagos, v_cuota_id, v_aplicar);

                UPDATE cuotas
                SET monto_pagado = v_nuevo_pagado,
                    estado = IF(v_nuevo_pagado >= monto_cuota, 'Pagada', 'Parcial'),
                    fecha_pago = IF(v_nuevo_pagado >= monto_cuota, NOW(), fecha_pago)
                WHERE cod_cuota = v_cuota_id;

                SET v_restante = v_restante - v_aplicar;
            END IF;
        END LOOP;

        CLOSE cur_cuotas;
    END IF;

    SELECT deuda_total INTO v_deuda_total
    FROM cuentas_por_cobrar
    WHERE cod_cuentas = p_cod_cuentas;

    SELECT IFNULL(SUM(monto_abonado), 0.00) INTO v_total_pagado_cuenta
    FROM pago_cuentas
    WHERE cod_cuentas = p_cod_cuentas
      AND estado IN ('Procesado', 'Aprobado');

    SET v_nueva_deuda = GREATEST(0.00, v_deuda_total - v_total_pagado_cuenta);

    UPDATE cuentas_por_cobrar
    SET deuda = v_nueva_deuda,
        estado = IF(v_nueva_deuda <= 0, 'Pagado', 'Pendiente')
    WHERE cod_cuentas = p_cod_cuentas;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_generar_cuotas` (IN `p_cod_cuentas` INT, IN `p_monto_financiar` DECIMAL(15,2), IN `p_cantidad_cuotas` INT, IN `p_frecuencia` VARCHAR(20), IN `p_fecha_inicio` DATE)   BEGIN
    DECLARE v_i INT DEFAULT 1;
    DECLARE v_monto_base DECIMAL(15,2);
    DECLARE v_monto_cuota DECIMAL(15,2);
    DECLARE v_fecha_venc DATE;
    DECLARE v_fecha_base DATE;
    DECLARE v_frec_norm VARCHAR(20);
    DECLARE v_pagos_existentes INT DEFAULT 0;

    IF p_cantidad_cuotas IS NULL OR p_cantidad_cuotas < 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cantidad de cuotas debe ser al menos 1.';
    END IF;

    IF p_monto_financiar IS NULL OR p_monto_financiar <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El monto a financiar debe ser mayor a 0.';
    END IF;

    SELECT COUNT(*) INTO v_pagos_existentes
    FROM cuotas
    WHERE cod_cuentas = p_cod_cuentas AND monto_pagado > 0;

    IF v_pagos_existentes > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se pueden regenerar las cuotas porque ya existen cuotas con pagos aplicados.';
    END IF;

    DELETE FROM cuotas WHERE cod_cuentas = p_cod_cuentas;

    SET v_frec_norm = LOWER(TRIM(IFNULL(p_frecuencia, 'mensual')));
    SET v_fecha_base = IFNULL(p_fecha_inicio, CURDATE());
    SET v_monto_base = ROUND(p_monto_financiar / p_cantidad_cuotas, 2);

    WHILE v_i <= p_cantidad_cuotas DO
        IF v_i = p_cantidad_cuotas THEN
            SET v_monto_cuota = p_monto_financiar - (v_monto_base * (p_cantidad_cuotas - 1));
        ELSE
            SET v_monto_cuota = v_monto_base;
        END IF;

        IF v_frec_norm = 'semanal' THEN
            SET v_fecha_venc = DATE_ADD(v_fecha_base, INTERVAL (v_i - 1) * 7 DAY);
        ELSEIF v_frec_norm = 'quincenal' THEN
            SET v_fecha_venc = DATE_ADD(v_fecha_base, INTERVAL (v_i - 1) * 15 DAY);
        ELSE
            SET v_fecha_venc = DATE_ADD(v_fecha_base, INTERVAL (v_i - 1) MONTH);
        END IF;

        INSERT INTO cuotas (cod_cuentas, numero_cuota, monto_cuota, monto_pagado, fecha_vencimiento, estado)
        VALUES (p_cod_cuentas, v_i, v_monto_cuota, 0.00, v_fecha_venc, 'Pendiente');

        SET v_i = v_i + 1;
    END WHILE;

    UPDATE cuentas_por_cobrar
    SET frecuencia_pago = CONCAT(UCASE(LEFT(v_frec_norm, 1)), SUBSTRING(v_frec_norm, 2)),
        cantidad_cuotas = p_cantidad_cuotas,
        fecha_inicio_cuotas = v_fecha_base,
        fecha_vencimiento = TIMESTAMP(v_fecha_venc, '23:59:59')
    WHERE cod_cuentas = p_cod_cuentas;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_listar_mantenimientos_detallados` (IN `p_estado_mantenimiento` VARCHAR(20), IN `p_cod_taller` INT, IN `p_placa` VARCHAR(20))   BEGIN
    SELECT
        m.cod_mantenimiento,
        m.descripcion_general,
        m.quien_autoriza,
        m.estado AS estado_mantenimiento,

        dm.cod_detalle,
        dm.tipo,
        dm.fecha_solicitud,
        dm.fecha_completada,

        v.placa,
        v.color,
        v.anio,
        v.kilometraje,
        v.estado AS estado_vehiculo,

        t.cod_taller,
        t.nombre_taller,
        t.direccion AS direccion_taller,
        t.estado AS estado_taller,

        dm.cedula_usuario
    FROM mantenimiento AS m
    INNER JOIN det_mantenimiento AS dm
        ON m.cod_mantenimiento = dm.cod_mantenimiento
    INNER JOIN vehiculo AS v
        ON dm.placa = v.placa
    INNER JOIN taller AS t
        ON dm.cod_taller = t.cod_taller
    WHERE (p_estado_mantenimiento IS NULL OR p_estado_mantenimiento = '' OR m.estado = p_estado_mantenimiento)
      AND (p_cod_taller IS NULL OR p_cod_taller = 0 OR dm.cod_taller = p_cod_taller)
      AND (p_placa IS NULL OR p_placa = '' OR dm.placa = p_placa)
    ORDER BY m.cod_mantenimiento DESC;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_listar_servicios_detallados` (IN `p_placa` VARCHAR(20), IN `p_estado` VARCHAR(20))   BEGIN
    SELECT
        s.cod_servicios,
        s.nombre_servicio,
        s.costo_base,
        s.estado,
        ds.cod_det_servicio,
        ds.costo_final,
        ds.descripcion_especifica,
        ds.fecha_realizacion,
        ds.placa,
        v.estado AS estado_vehiculo
    FROM servicios s
    LEFT JOIN det_servicios ds ON ds.cod_servicios = s.cod_servicios
    LEFT JOIN vehiculo v ON v.placa = ds.placa
    WHERE (p_placa IS NULL OR p_placa = '' OR ds.placa = p_placa)
      AND (p_estado IS NULL OR p_estado = '' OR s.estado = p_estado)
    ORDER BY s.cod_servicios DESC;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_listar_ventas` (IN `p_placa` VARCHAR(20), IN `p_estado` VARCHAR(45))   BEGIN
    SELECT
       v.cod_venta,
       v.estado AS estado_venta,
       v.fecha_venta,
       v.tipo_venta,
       v.cedula_usuario AS usuario_registro,
       dv.cod_det_venta,
       dv.precio AS precio_venta,
       dv.traspaso_papel,
       dv.placa,
       veh.color AS color_vehiculo,
       veh.anio AS anio_vehiculo,
       cxc.cod_cuentas,
       cxc.deuda_total,
       cxc.monto_inicial,
       cxc.deuda,
       cxc.frecuencia_pago,
       cxc.cantidad_cuotas,
       cxc.estado AS estado_cuenta
    FROM ventas v
    LEFT JOIN det_venta dv ON dv.cod_venta = v.cod_venta
    LEFT JOIN vehiculo veh ON veh.placa = dv.placa
    LEFT JOIN cuentas_por_cobrar cxc ON cxc.cod_venta = v.cod_venta
    WHERE (p_placa IS NULL OR p_placa = '' OR dv.placa = p_placa)
      AND (p_estado IS NULL OR p_estado = '' OR v.estado = p_estado)
    ORDER BY v.cod_venta DESC;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_obtener_catalogo_detallado` (IN `p_placa` VARCHAR(10), IN `p_solo_disponibles` BOOLEAN)   BEGIN
    SELECT 
        v.placa, v.anio, v.estado, v.color,
        ma.nombre_marca, mo.nombre_modelo, 
        i.URL as imagen_url, 
        c.precio, c.descripcion, c.fecha_publicacion,
        d.fecha_ingreso,
        p.razon_social as nombre_propietario
    FROM vehiculo v
    JOIN catalogo c ON v.placa = c.placa
    JOIN modelo mo ON v.cod_modelo = mo.cod_modelo
    JOIN marca ma ON mo.cod_marca = ma.cod_marca
    JOIN documentacion d ON v.cod_documento = d.cod_documento
    JOIN propietario p ON v.cedula_propietario = p.cedula_propietario
    LEFT JOIN imagen i ON v.placa = i.placa
    WHERE v.estado != 'Inactivo'
    
    AND (p_placa IS NULL OR v.placa = p_placa)
    AND (p_solo_disponibles = FALSE OR v.estado = 'Disponible')
    ORDER BY c.fecha_publicacion DESC;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_obtener_historial_vehiculos` ()   BEGIN
    SELECT 
        h.cod_historia,
        h.placa,
        h.estado,
        h.fecha_cambio,
        h.observaciones,
        ma.nombre_marca,
        mo.nombre_modelo,
        v.color
    FROM historia_estado_vehiculo h
    JOIN vehiculo v ON h.placa = v.placa
    JOIN modelo mo ON v.cod_modelo = mo.cod_modelo
    JOIN marca ma ON mo.cod_marca = ma.cod_marca
    ORDER BY h.fecha_cambio DESC;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_registrar_cliente` (IN `p_cedula` VARCHAR(20), IN `p_nombre` VARCHAR(50), IN `p_apellido` VARCHAR(50), IN `p_telefono` VARCHAR(20), IN `p_direccion` VARCHAR(255), IN `p_correo` VARCHAR(100), IN `p_password` VARCHAR(255), IN `p_foto` VARCHAR(255), OUT `p_resultado` VARCHAR(100))   BEGIN
    DECLARE existe_cedula INT DEFAULT 0;
    DECLARE existe_correo INT DEFAULT 0;

    SELECT COUNT(*) INTO existe_cedula FROM seguridad.t_usuario WHERE cedula_usuario = p_cedula;
    SELECT COUNT(*) INTO existe_correo FROM seguridad.t_usuario WHERE correo = p_correo;

    IF existe_cedula > 0 THEN
        SET p_resultado = 'ERROR: La cédula ya se encuentra registrada en el sistema.';
    ELSEIF existe_correo > 0 THEN
        SET p_resultado = 'ERROR: El correo electrónico ya pertenece a otro usuario.';
    ELSE
        INSERT INTO seguridad.t_usuario (cedula_usuario, nombre, apellido, telefono, direccion, correo, password, foto, cod_rol, estado)
        VALUES (p_cedula, p_nombre, p_apellido, p_telefono, p_direccion, p_correo, p_password, p_foto, 4, 1);
        SET p_resultado = 'OK: Cliente registrado exitosamente.';
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_registrar_credito_con_cuotas` (IN `p_cod_venta` INT, IN `p_precio_total` DECIMAL(15,2), IN `p_monto_inicial` DECIMAL(15,2), IN `p_tasa_interes` DECIMAL(5,2), IN `p_frecuencia` VARCHAR(20), IN `p_cantidad_cuotas` INT, IN `p_fecha_emision` DATE, IN `p_fecha_inicio_cuotas` DATE, OUT `p_cod_cuentas` INT)   BEGIN
    DECLARE v_inicial DECIMAL(15,2);
    DECLARE v_interes DECIMAL(15,2);
    DECLARE v_saldo_base DECIMAL(15,2);
    DECLARE v_monto_interes DECIMAL(15,2);
    DECLARE v_deuda_total DECIMAL(15,2);
    DECLARE v_saldo_financiar DECIMAL(15,2);

    SET v_inicial = IFNULL(p_monto_inicial, 0.00);
    SET v_interes = IFNULL(p_tasa_interes, 0.00);
    SET v_saldo_base = GREATEST(0.00, p_precio_total - v_inicial);
    SET v_monto_interes = ROUND(v_saldo_base * (v_interes / 100), 2);
    SET v_deuda_total = p_precio_total + v_monto_interes;
    SET v_saldo_financiar = v_deuda_total - v_inicial;

    INSERT INTO cuentas_por_cobrar (
        deuda_total,
        monto_inicial,
        tasa_interes,
        frecuencia_pago,
        cantidad_cuotas,
        fecha_vencimiento,
        fecha_emision,
        fecha_inicio_cuotas,
        estado,
        cod_venta,
        deuda
    ) VALUES (
        v_deuda_total,
        v_inicial,
        v_interes,
        IFNULL(p_frecuencia, 'Mensual'),
        IFNULL(p_cantidad_cuotas, 1),
        NULL,
        IFNULL(p_fecha_emision, CURDATE()),
        p_fecha_inicio_cuotas,
        IF(v_saldo_financiar <= 0, 'Pagado', 'Pendiente'),
        p_cod_venta,
        v_saldo_financiar
    );

    SET p_cod_cuentas = LAST_INSERT_ID();

    IF v_saldo_financiar > 0 THEN
        CALL sp_generar_cuotas(
            p_cod_cuentas,
            v_saldo_financiar,
            IFNULL(p_cantidad_cuotas, 1),
            IFNULL(p_frecuencia, 'Mensual'),
            p_fecha_inicio_cuotas
        );
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_registrar_cuenta_cobrar` (IN `p_cod_venta` INT, IN `p_deuda_total` DECIMAL(15,2), IN `p_fecha_vencimiento` DATETIME, IN `p_fecha_emision` DATE)   BEGIN
    INSERT INTO cuentas_por_cobrar (deuda_total, fecha_vencimiento, fecha_emision, estado, cod_venta, deuda)
    VALUES (p_deuda_total, p_fecha_vencimiento, p_fecha_emision, 'Pendiente', p_cod_venta, p_deuda_total);
END$$

--
-- Funciones
--
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_calcular_costo_total_servicio` (`p_cod_servicio` INT) RETURNS DECIMAL(10,2) DETERMINISTIC READS SQL DATA BEGIN
    DECLARE v_costo_total DECIMAL(10,2);

    SELECT COALESCE(SUM(ds.costo_final), 0)
    INTO v_costo_total
    FROM det_servicios ds
    WHERE ds.cod_servicios = p_cod_servicio;

    RETURN v_costo_total;
END$$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_citas_en_horario` (`p_fecha` DATE, `p_hora` TIME) RETURNS INT(11) DETERMINISTIC READS SQL DATA BEGIN
    DECLARE total_citas INT DEFAULT 0;
    SELECT COUNT(*) INTO total_citas 
    FROM automall.citas 
    WHERE fecha = p_fecha AND hora = p_hora AND activo = 1;
    RETURN total_citas;
END$$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_cliente_tiene_citas_activas` (`p_cedula` VARCHAR(20)) RETURNS TINYINT(1) DETERMINISTIC READS SQL DATA BEGIN
    DECLARE total_activas INT DEFAULT 0;
    SELECT COUNT(*) INTO total_activas 
    FROM automall.citas 
    WHERE cedula_usuario = p_cedula AND estado = 'Pendiente' AND activo = 1;
    
    IF total_activas > 0 THEN
        RETURN 1;
    ELSE
        RETURN 0;
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_contar_mantenimientos_por_taller` (`p_cod_taller` INT) RETURNS INT(11) DETERMINISTIC READS SQL DATA BEGIN
    DECLARE v_cantidad INT;

    SELECT COUNT(*)
    INTO v_cantidad
    FROM det_mantenimiento dm
    WHERE dm.cod_taller = p_cod_taller;

    RETURN v_cantidad;
END$$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_cuotas_pendientes_cuenta` (`p_cod_cuentas` INT) RETURNS INT(11) DETERMINISTIC READS SQL DATA BEGIN
    DECLARE v_cantidad INT DEFAULT 0;

    SELECT COUNT(*) INTO v_cantidad
    FROM cuotas
    WHERE cod_cuentas = p_cod_cuentas
      AND estado IN ('Pendiente', 'Parcial', 'Vencida');

    RETURN v_cantidad;
END$$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_monto_vencido_cuenta` (`p_cod_cuentas` INT) RETURNS DECIMAL(15,2) DETERMINISTIC READS SQL DATA BEGIN
    DECLARE v_vencido DECIMAL(15,2) DEFAULT 0.00;

    SELECT IFNULL(SUM(GREATEST(0, monto_cuota - monto_pagado)), 0.00) INTO v_vencido
    FROM cuotas
    WHERE cod_cuentas = p_cod_cuentas
      AND estado IN ('Pendiente', 'Parcial', 'Vencida')
      AND fecha_vencimiento < CURDATE();

    RETURN v_vencido;
END$$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_obtener_deuda_venta` (`p_cod_venta` INT) RETURNS DECIMAL(12,2) DETERMINISTIC BEGIN
    DECLARE v_deuda DECIMAL(12,2);
    
    SELECT deuda INTO v_deuda
    FROM cuentas_por_cobrar
    WHERE cod_venta = p_cod_venta
    LIMIT 1;
    
    RETURN IFNULL(v_deuda, 0);
END$$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_total_pagado_cliente` (`p_cedula` VARCHAR(20)) RETURNS DECIMAL(15,2) DETERMINISTIC READS SQL DATA BEGIN
    DECLARE v_total_pagado DECIMAL(15,2);

    SELECT SUM(pc.monto_abonado) INTO v_total_pagado
    FROM pago_cuentas pc
    INNER JOIN cuentas_por_cobrar cxc ON pc.cod_cuentas = cxc.cod_cuentas
    INNER JOIN ventas v ON cxc.cod_venta = v.cod_venta
    WHERE v.cedula_usuario = p_cedula
      AND pc.estado IN ('Procesado', 'Aprobado');

    RETURN IFNULL(v_total_pagado, 0.00);
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `accesorio`
--

CREATE TABLE `accesorio` (
  `cod_accesorio` int(11) NOT NULL,
  `copia_llaves` tinyint(1) DEFAULT 0,
  `repuesto` tinyint(1) DEFAULT 0,
  `triangulo` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `accesorio`
--

INSERT INTO `accesorio` (`cod_accesorio`, `copia_llaves`, `repuesto`, `triangulo`) VALUES
(1, 1, 1, 1),
(2, 1, 0, 1),
(3, 1, 1, 0),
(4, 0, 1, 1),
(5, 1, 1, 1),
(6, 1, 0, 0),
(7, 0, 0, 1),
(8, 1, 1, 1),
(9, 1, 0, 1),
(10, 1, 0, 0),
(11, 1, 1, 0),
(12, 0, 1, 1),
(13, 1, 0, 1),
(14, 0, 1, 0),
(15, 1, 1, 1),
(16, 1, 0, 0),
(17, 0, 1, 1),
(18, 1, 1, 1),
(19, 1, 1, 0),
(20, 0, 0, 1),
(25, 0, 1, 0),
(26, 1, 1, 1),
(27, 1, 1, 0),
(28, 0, 1, 1),
(30, 1, 1, 1),
(31, 1, 0, 1),
(32, 1, 1, 0),
(33, 0, 1, 1),
(34, 1, 1, 1),
(35, 1, 0, 0),
(36, 0, 0, 1),
(37, 1, 1, 1),
(38, 1, 0, 1),
(39, 0, 1, 0),
(40, 1, 1, 1),
(41, 1, 1, 0),
(42, 1, 0, 1),
(43, 0, 1, 1),
(44, 1, 1, 1),
(45, 1, 0, 0),
(46, 0, 1, 1),
(47, 1, 1, 1),
(48, 1, 1, 0),
(49, 0, 0, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `banco`
--

CREATE TABLE `banco` (
  `cod_banco` int(11) NOT NULL,
  `cod_oficial` int(11) NOT NULL,
  `nombre_banco` varchar(100) NOT NULL,
  `estado` varchar(20) DEFAULT 'Activo',
  `fecha_registro` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `banco`
--

INSERT INTO `banco` (`cod_banco`, `cod_oficial`, `nombre_banco`, `estado`, `fecha_registro`) VALUES
(1, 0, 'Provincial', 'Activo', '0000-00-00'),
(2, 0, 'Banesco', 'Activo', '0000-00-00');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `catalogo`
--

CREATE TABLE `catalogo` (
  `cod_catalogo` int(11) NOT NULL,
  `estado` varchar(50) DEFAULT 'Disponible',
  `precio` decimal(10,2) DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  `fecha_publicacion` date NOT NULL,
  `placa` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `catalogo`
--

INSERT INTO `catalogo` (`cod_catalogo`, `estado`, `precio`, `descripcion`, `fecha_publicacion`, `placa`) VALUES
(6, 'vendido', 5000.00, 'todo fino', '2026-07-07', 'YUHH544'),
(7, 'vendido', 5000.00, 'demasiado bueno', '2026-07-07', 'ksokqw28'),
(8, 'vendido', 50000.00, 'chukiluki', '2026-08-31', 'FJA-KSK'),
(9, 'vendido', 30000.04, 'compralo o compralo', '2026-05-30', 'YUY66767'),
(30, 'vendido', 12000.00, 'Vehículo en excelente estado, único dueño.', '2026-09-01', 'AB123CD'),
(31, 'vendido', 15000.00, 'Full extras, mantenimiento al día.', '2026-09-02', 'EF456GH'),
(32, 'vendido', 11000.00, 'Ideal para ciudad, bajo consumo.', '2026-09-03', 'IJ789KL'),
(33, 'Activo', 18000.00, 'SUV amplia, perfecta para familia.', '2026-09-04', 'MN012OP'),
(34, 'Activo', 13500.00, 'Pick-up de trabajo, motor fuerte.', '2026-09-05', 'QR345ST'),
(35, 'Activo', 16000.00, 'Coupé deportivo, recién importado.', '2026-09-06', 'UV678WX'),
(36, 'Activo', 9500.00, 'Económico y confiable.', '2026-09-07', 'YZ901AB'),
(37, 'vendido', 12500.00, 'Sedán cómodo, papeles al día.', '2026-09-08', 'CD234EF'),
(38, 'Activo', 14000.00, 'Vehículo premium, única mano.', '2026-09-09', 'GH567IJ'),
(39, 'Activo', 15500.00, 'Recién importado, sin detalles.', '2026-09-10', 'KL890MN'),
(40, 'Activo', 17500.00, 'Deportivo, excelente rendimiento.', '2026-09-11', 'OP123QR'),
(41, 'Activo', 13000.00, 'Familiar, económico y seguro.', '2026-09-11', 'ST456UV'),
(42, 'Activo', 11500.00, 'Todo terreno, ideal para viajes.', '2026-09-12', 'WX789YZ'),
(43, 'vendido', 14500.00, 'Ejecutivo, acabados de lujo.', '2026-09-12', 'AB012CD'),
(44, 'vendido', 10000.00, 'Práctico y versátil.', '2026-09-12', 'EF345GH'),
(45, 'Activo', 16500.00, 'Compacto, fácil de estacionar.', '2026-09-12', 'IJ678KL'),
(46, 'Activo', 15000.00, 'Full equipo, listo para estrenar.', '2026-09-12', 'MN901OP'),
(47, 'Activo', 12000.00, 'Vehículo de agencia, garantía vigente.', '2026-09-12', 'QR234ST'),
(48, 'Activo', 13500.00, 'Deportivo biplaza.', '2026-09-12', 'UV567WX'),
(49, 'Activo', 17000.00, 'Alta gama, único en su clase.', '2026-09-12', 'YZ890AB');

--
-- Disparadores `catalogo`
--
DELIMITER $$
CREATE TRIGGER `tg_copiar_fecha_ingreso_a_catalogo` BEFORE INSERT ON `catalogo` FOR EACH ROW BEGIN
    DECLARE fecha_ing DATE;

    -- Buscamos la fecha de ingreso en la tabla documentacion 
    -- relacionando la placa del catálogo con el vehículo
    SELECT d.fecha_ingreso INTO fecha_ing
    FROM vehiculo v
    JOIN documentacion d ON v.cod_documento = d.cod_documento
    WHERE v.placa = NEW.placa;

    IF fecha_ing IS NOT NULL THEN
        SET NEW.fecha_publicacion = fecha_ing;
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `citas`
--

CREATE TABLE `citas` (
  `cod_citas` int(11) NOT NULL,
  `estado` varchar(20) DEFAULT 'Pendiente',
  `fecha` date NOT NULL,
  `hora` time DEFAULT NULL,
  `cod_catalogo` int(11) DEFAULT NULL,
  `cedula_usuario` varchar(20) NOT NULL,
  `activo` int(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `citas`
--

INSERT INTO `citas` (`cod_citas`, `estado`, `fecha`, `hora`, `cod_catalogo`, `cedula_usuario`, `activo`) VALUES
(2, 'Pendiente', '2026-07-08', '11:00:00', 6, '29880513', 0),
(3, 'Pendiente', '2026-08-27', '08:00:00', 6, '18998754', 1),
(4, 'Pendiente', '2026-09-17', '13:00:00', 7, '29880513', 1);

--
-- Disparadores `citas`
--
DELIMITER $$
CREATE TRIGGER `trg_cita_validar_horario_limit` BEFORE INSERT ON `citas` FOR EACH ROW BEGIN
    IF NEW.activo = 1 AND automall.fn_citas_en_horario(NEW.fecha, NEW.hora) >= 3 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Operación denegada: El horario seleccionado ya cuenta con el cupo máximo de 3 citas simultáneas.';
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `compras_accesorios`
--

CREATE TABLE `compras_accesorios` (
  `cod_compras` int(11) NOT NULL,
  `fecha_compra` date NOT NULL,
  `precio` decimal(20,2) DEFAULT NULL,
  `tipo_compra` varchar(50) NOT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `observaciones` varchar(100) NOT NULL,
  `rif_cedula_proveedor` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `compras_accesorios`
--

INSERT INTO `compras_accesorios` (`cod_compras`, `fecha_compra`, `precio`, `tipo_compra`, `estado`, `observaciones`, `rif_cedula_proveedor`) VALUES
(1, '2026-09-11', 0.00, 'Normal', 'Completada', 'jdfhjsdhfjkshfkjs', 23685946),
(2, '2026-09-11', 0.00, 'Urgente', 'Completada', 'dfvdfvdfv', 23685946),
(3, '2026-09-11', 0.00, 'Mantenimiento', 'Completada', '', 23685946),
(4, '2026-09-11', 0.00, 'Normal', 'Anulada', 'dgfedge', 2424242),
(5, '2026-11-24', 0.00, 'Urgente', 'Pendiente', '', 2424242);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cuentas_por_cobrar`
--

CREATE TABLE `cuentas_por_cobrar` (
  `cod_cuentas` int(11) NOT NULL,
  `deuda_total` decimal(15,2) NOT NULL DEFAULT 0.00,
  `monto_inicial` decimal(15,2) NOT NULL DEFAULT 0.00,
  `tasa_interes` decimal(5,2) NOT NULL DEFAULT 0.00,
  `frecuencia_pago` varchar(20) NOT NULL DEFAULT 'Contado',
  `cantidad_cuotas` int(11) NOT NULL DEFAULT 1,
  `fecha_vencimiento` datetime DEFAULT NULL,
  `fecha_emision` date NOT NULL,
  `fecha_inicio_cuotas` date DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'Pendiente',
  `cod_venta` int(11) DEFAULT NULL,
  `deuda` decimal(15,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cuentas_por_cobrar`
--

INSERT INTO `cuentas_por_cobrar` (`cod_cuentas`, `deuda_total`, `monto_inicial`, `tasa_interes`, `frecuencia_pago`, `cantidad_cuotas`, `fecha_vencimiento`, `fecha_emision`, `fecha_inicio_cuotas`, `estado`, `cod_venta`, `deuda`) VALUES
(1, 5000.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-09-11', NULL, 'anulada', 1, 0.00),
(2, 50000.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-09-12', NULL, 'pagado', 2, 0.00),
(3, 31000.04, 0.00, 0.00, 'Contado', 1, '2026-12-02 00:00:00', '2026-09-12', NULL, 'Anulado', 3, 9800.04),
(4, 5000.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-09-12', NULL, 'anulada', 4, 0.00),
(5, 5000.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-09-12', NULL, 'anulada', 5, 0.00),
(6, 5000.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-09-12', NULL, 'pagado', 6, 0.00),
(7, 5000.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-09-12', NULL, 'pagado', 7, 0.00),
(8, 10000.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-09-13', NULL, 'Anulado', 8, 10000.00),
(9, 14500.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-09-14', NULL, 'pagado', 9, 0.00),
(10, 15000.00, 0.00, 0.00, 'Contado', 1, '2026-11-11 00:00:00', '2026-09-17', NULL, 'Pendiente', 10, 4819.93),
(11, 12500.00, 0.00, 0.00, 'Contado', 1, '2026-09-30 00:00:00', '2026-09-17', NULL, 'pendiente', 11, 6599.91),
(12, 10000.00, 0.00, 0.00, 'Contado', 1, '2026-11-30 00:00:00', '2026-09-17', NULL, 'pendiente', 12, 4689.92),
(13, 15000.00, 0.00, 0.00, 'Contado', 1, '0000-00-00 00:00:00', '2026-10-20', NULL, 'pagado', 13, 0.00),
(14, 12980.00, 1100.00, 20.00, 'Mensual', 12, '2027-12-22 23:59:59', '2026-11-22', '2027-01-22', 'Pendiente', 14, 9900.00);

--
-- Disparadores `cuentas_por_cobrar`
--
DELIMITER $$
CREATE TRIGGER `trg_after_update_cxc_anulada` AFTER UPDATE ON `cuentas_por_cobrar` FOR EACH ROW BEGIN
    IF LOWER(OLD.estado) NOT IN ('anulado', 'anulada')
       AND LOWER(NEW.estado) IN ('anulado', 'anulada') THEN
        UPDATE cuotas
        SET estado = 'Anulada'
        WHERE cod_cuentas = NEW.cod_cuentas
          AND estado IN ('Pendiente', 'Parcial', 'Vencida');
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cuotas`
--

CREATE TABLE `cuotas` (
  `cod_cuota` int(11) NOT NULL,
  `cod_cuentas` int(11) NOT NULL,
  `numero_cuota` int(11) NOT NULL,
  `monto_cuota` decimal(15,2) NOT NULL,
  `monto_pagado` decimal(15,2) NOT NULL DEFAULT 0.00,
  `fecha_vencimiento` date NOT NULL,
  `fecha_pago` datetime DEFAULT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'Pendiente',
  `observaciones` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cuotas`
--

INSERT INTO `cuotas` (`cod_cuota`, `cod_cuentas`, `numero_cuota`, `monto_cuota`, `monto_pagado`, `fecha_vencimiento`, `fecha_pago`, `estado`, `observaciones`) VALUES
(1, 14, 1, 990.00, 990.00, '2027-01-22', '2026-11-22 23:28:40', 'Pagada', NULL),
(2, 14, 2, 990.00, 990.00, '2027-02-22', '2026-11-24 16:44:48', 'Pagada', NULL),
(3, 14, 3, 990.00, 0.00, '2027-03-22', NULL, 'Pendiente', NULL),
(4, 14, 4, 990.00, 0.00, '2027-04-22', NULL, 'Pendiente', NULL),
(5, 14, 5, 990.00, 0.00, '2027-05-22', NULL, 'Pendiente', NULL),
(6, 14, 6, 990.00, 0.00, '2027-06-22', NULL, 'Pendiente', NULL),
(7, 14, 7, 990.00, 0.00, '2027-07-22', NULL, 'Pendiente', NULL),
(8, 14, 8, 990.00, 0.00, '2027-08-22', NULL, 'Pendiente', NULL),
(9, 14, 9, 990.00, 0.00, '2027-09-22', NULL, 'Pendiente', NULL),
(10, 14, 10, 990.00, 0.00, '2027-10-22', NULL, 'Pendiente', NULL),
(11, 14, 11, 990.00, 0.00, '2027-11-22', NULL, 'Pendiente', NULL),
(12, 14, 12, 990.00, 0.00, '2027-12-22', NULL, 'Pendiente', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `det_banco`
--

CREATE TABLE `det_banco` (
  `cod_det_banco` int(11) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `referencia` varchar(255) DEFAULT NULL,
  `cod_banco` int(11) NOT NULL,
  `cod_det_pago` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `det_banco`
--

INSERT INTO `det_banco` (`cod_det_banco`, `monto`, `referencia`, `cod_banco`, `cod_det_pago`) VALUES
(1, 14500.00, '1213245315', 2, 9),
(2, 5310.08, '12345688888', 1, 15),
(3, 910624.47, '54545454', 1, 20);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `det_compra`
--

CREATE TABLE `det_compra` (
  `cod_det_compra` int(11) NOT NULL,
  `cantidad` int(11) DEFAULT NULL,
  `cod_insumo` int(11) NOT NULL,
  `cod_compras` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `det_compra`
--

INSERT INTO `det_compra` (`cod_det_compra`, `cantidad`, `cod_insumo`, `cod_compras`) VALUES
(1, 1, 2, 1),
(2, 2, 3, 2),
(3, 5, 2, 3),
(4, 1, 3, 3),
(5, 5, 2, 4),
(6, 4, 4, 4),
(7, 1, 2, 5);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `det_mantenimiento`
--

CREATE TABLE `det_mantenimiento` (
  `cod_detalle` int(11) NOT NULL,
  `tipo` varchar(20) NOT NULL,
  `fecha_solicitud` date NOT NULL,
  `fecha_completada` date DEFAULT NULL,
  `cod_mantenimiento` int(11) DEFAULT NULL,
  `placa` varchar(20) NOT NULL,
  `cod_taller` int(11) NOT NULL,
  `cedula_usuario` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `det_mantenimiento`
--

INSERT INTO `det_mantenimiento` (`cod_detalle`, `tipo`, `fecha_solicitud`, `fecha_completada`, `cod_mantenimiento`, `placa`, `cod_taller`, `cedula_usuario`) VALUES
(1, 'Preventivo', '2026-07-09', '2026-11-24', 1, 'YUHH544', 1, '29880513'),
(2, 'Preventivo', '2026-09-11', '2026-09-12', 2, 'YUHH544', 1, '14094670'),
(3, 'Preventivo', '2026-11-24', NULL, 3, 'IJ678KL', 2, '18998754');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `det_nom_digital`
--

CREATE TABLE `det_nom_digital` (
  `cod_det_digital` int(11) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `referencia` varchar(255) DEFAULT NULL,
  `cod_mon_digital` int(11) NOT NULL,
  `cod_det_pago` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `det_nom_digital`
--

INSERT INTO `det_nom_digital` (`cod_det_digital`, `monto`, `referencia`, `cod_mon_digital`, `cod_det_pago`) VALUES
(1, 5000.00, '3433444', 2, 1),
(2, 50000.00, '1235454', 2, 2),
(3, 20000.00, '2121212', 2, 3),
(4, 5000.00, '', 1, 4),
(5, 5000.00, '1345445646', 2, 5),
(6, 5000.00, '12345688888', 2, 6),
(7, 5000.00, '154896456', 3, 7),
(8, 1200.00, '12345SA6D4S5A64D5A', 2, 10),
(9, 3100.00, 'DA1D2A31D5S6A', 1, 11),
(10, 1850.00, '', 1, 12),
(11, 4200.00, 'F245645FDS45GD4G6DG4', 1, 16),
(12, 15000.00, '', 1, 17),
(13, 1100.00, '', 1, 18),
(14, 990.00, '123459887897899', 1, 19);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `det_pago`
--

CREATE TABLE `det_pago` (
  `cod_det_pago` int(11) NOT NULL,
  `tipo_pago` varchar(20) NOT NULL,
  `fecha_det_pago` datetime NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `cod_pagos` int(11) NOT NULL,
  `cod_metodo` int(11) NOT NULL,
  `cod_moneda` int(250) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `det_pago`
--

INSERT INTO `det_pago` (`cod_det_pago`, `tipo_pago`, `fecha_det_pago`, `descripcion`, `cod_pagos`, `cod_metodo`, `cod_moneda`) VALUES
(1, 'contado', '2026-09-11 12:31:09', 'Pago inicial - Venta contado', 1, 4, NULL),
(2, 'contado', '2026-09-12 21:41:41', 'Pago inicial - Venta contado', 2, 4, NULL),
(3, 'credito', '2026-09-12 21:44:28', 'Pago inicial - Venta credito', 3, 4, NULL),
(4, 'contado', '2026-09-12 22:48:30', 'Pago inicial - Venta contado\n[ANULADO] Motivo: ocurrio un problema', 4, 1, NULL),
(5, 'contado', '2026-09-12 22:58:23', 'Pago inicial - Venta contado\n[ANULADO] Motivo: error en transferencia', 5, 4, NULL),
(6, 'contado', '2026-09-12 23:03:08', 'Pago inicial - Venta contado', 6, 4, NULL),
(7, 'contado', '2026-09-12 23:11:45', 'Pago inicial - Venta contado', 7, 6, NULL),
(8, 'contado', '2026-09-13 00:23:11', 'Pago inicial - Venta contado\n[ANULADO] Motivo: Error devuelto el pago por orden', 8, 2, 1),
(9, 'contado', '2026-09-14 00:23:50', 'Pago inicial - Venta contado', 9, 3, 1),
(10, 'abono', '2026-09-15 22:12:44', 'ajdksajdkadjakldja', 10, 4, NULL),
(11, 'abono', '2026-09-15 22:47:34', 'Yo se lo pague\n[ANULADO] Motivo: No estoy haciendo una prueba', 11, 1, NULL),
(12, 'credito', '2026-09-17 12:39:01', 'Pago inicial - Venta credito', 12, 1, NULL),
(13, 'abono', '2026-09-17 12:40:42', 'pAGO UNA PARTE DE LA DEUDA | Monto recibido: 3500000.00 Bs. | Tasa: 847.444200 Bs/USD | Equivalente USD: $4130.07', 13, 2, 2),
(14, 'credito', '2026-09-17 13:12:51', 'Pago inicial - Venta credito', 14, 2, 2),
(15, 'credito', '2026-09-17 13:35:05', 'Pago inicial - Venta credito', 15, 5, 2),
(16, 'abono', '2026-09-17 13:44:33', 'sfkjdskfjsjsfjlsjfsljflsfjsjf', 16, 1, NULL),
(17, 'contado', '2026-10-20 21:44:55', 'Pago inicial - Venta contado', 17, 1, NULL),
(18, 'credito', '2026-11-22 22:23:55', 'Pago inicial - Venta credito', 18, 1, NULL),
(19, 'abono', '2026-11-22 23:28:40', 'Abono de cuenta', 19, 1, NULL),
(20, 'abono', '2026-11-24 16:44:48', 'Monto recibido: 910624.47 Bs. | Tasa: 919.822700 Bs/USD | Equivalente USD: $990.00', 20, 3, 2);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `det_salida`
--

CREATE TABLE `det_salida` (
  `cod_salida` int(11) NOT NULL,
  `fecha_salida` date NOT NULL,
  `cantidad_usada` int(50) NOT NULL,
  `descrpcion` varchar(250) NOT NULL,
  `placa` varchar(20) NOT NULL,
  `cod_insumo` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `det_servicios`
--

CREATE TABLE `det_servicios` (
  `cod_det_servicio` int(11) NOT NULL,
  `costo_final` decimal(10,2) DEFAULT NULL,
  `descripcion_especifica` varchar(250) DEFAULT NULL,
  `fecha_realizacion` date NOT NULL,
  `placa` varchar(20) NOT NULL,
  `cod_servicios` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `det_servicios`
--

INSERT INTO `det_servicios` (`cod_det_servicio`, `costo_final`, `descripcion_especifica`, `fecha_realizacion`, `placa`, `cod_servicios`) VALUES
(1, 50000.00, 'ksskkskssks', '2026-07-09', 'YUHH544', 1),
(2, 50.00, 'para que este atractivo a la venta', '2026-09-12', 'YUHH544', 2);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `det_venta`
--

CREATE TABLE `det_venta` (
  `cod_det_venta` int(11) NOT NULL,
  `poder` tinyint(1) DEFAULT 0,
  `traspaso_papel` tinyint(1) DEFAULT 0,
  `precio` decimal(12,2) NOT NULL,
  `placa` varchar(20) DEFAULT NULL,
  `cod_venta` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `det_venta`
--

INSERT INTO `det_venta` (`cod_det_venta`, `poder`, `traspaso_papel`, `precio`, `placa`, `cod_venta`) VALUES
(1, 1, 1, 5000.00, 'ksokqw28', 1),
(2, 0, 0, 50000.00, 'FJA-KSK', 2),
(3, 0, 1, 30000.04, 'YUY66767', 3),
(4, 1, 1, 5000.00, 'YUHH544', 4),
(5, 1, 1, 5000.00, 'YUHH544', 5),
(6, 1, 1, 5000.00, 'ksokqw28', 6),
(7, 1, 1, 5000.00, 'YUHH544', 7),
(8, 1, 1, 10000.00, 'EF345GH', 8),
(9, 1, 1, 14500.00, 'AB012CD', 9),
(10, 1, 1, 12000.00, 'AB123CD', 10),
(11, 1, 1, 12500.00, 'CD234EF', 11),
(12, 1, 1, 10000.00, 'EF345GH', 12),
(13, 1, 1, 15000.00, 'EF456GH', 13),
(14, 1, 1, 11000.00, 'IJ789KL', 14);

--
-- Disparadores `det_venta`
--
DELIMITER $$
CREATE TRIGGER `trg_actualizar_catalogo_venta` AFTER INSERT ON `det_venta` FOR EACH ROW BEGIN
    UPDATE catalogo 
    SET estado = 'vendido' 
    WHERE placa = NEW.placa;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `documentacion`
--

CREATE TABLE `documentacion` (
  `cod_documento` int(11) NOT NULL,
  `original_totalPropiedad` tinyint(1) DEFAULT 0,
  `experticia_transito` tinyint(1) DEFAULT 0,
  `certificado_origen` tinyint(1) DEFAULT 0,
  `carnet_circulacion` tinyint(1) DEFAULT 0,
  `reserva_dominio` tinyint(1) DEFAULT 0,
  `garantia_vehiculo` tinyint(1) DEFAULT 0,
  `certificado_garantia` tinyint(1) DEFAULT 0,
  `manual_vehiculoGarantia` tinyint(1) DEFAULT 0,
  `finiquito` tinyint(1) DEFAULT 0,
  `resguardo` tinyint(1) DEFAULT 0,
  `fecha_transferencia` tinyint(1) DEFAULT 0,
  `seguro` tinyint(1) DEFAULT 0,
  `factura_compra` tinyint(1) DEFAULT 0,
  `fecha_ingreso` date NOT NULL,
  `otro_documento` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `documentacion`
--

INSERT INTO `documentacion` (`cod_documento`, `original_totalPropiedad`, `experticia_transito`, `certificado_origen`, `carnet_circulacion`, `reserva_dominio`, `garantia_vehiculo`, `certificado_garantia`, `manual_vehiculoGarantia`, `finiquito`, `resguardo`, `fecha_transferencia`, `seguro`, `factura_compra`, `fecha_ingreso`, `otro_documento`) VALUES
(10, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, '2026-07-07', ''),
(11, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, '2026-07-07', ''),
(12, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, '2026-08-31', 'nada que opinar'),
(14, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, '2026-05-30', ''),
(30, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-01', NULL),
(31, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, '2026-09-02', NULL),
(32, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-03', NULL),
(33, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, '2026-09-04', NULL),
(34, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, '2026-09-05', NULL),
(35, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-06', NULL),
(36, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, '2026-09-07', NULL),
(37, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, '2026-09-08', NULL),
(38, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-09', NULL),
(39, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-10', NULL),
(40, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, '2026-09-11', NULL),
(41, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-11', NULL),
(42, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-12', NULL),
(43, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, '2026-09-12', NULL),
(44, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-12', NULL),
(45, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, '2026-09-12', NULL),
(46, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, '2026-09-12', NULL),
(47, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-12', NULL),
(48, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, '2026-09-12', NULL),
(49, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, '2026-09-12', NULL);

--
-- Disparadores `documentacion`
--
DELIMITER $$
CREATE TRIGGER `tg_actualizar_fecha_catalogo` AFTER UPDATE ON `documentacion` FOR EACH ROW BEGIN
    -- Si la fecha de ingreso cambió en la tabla documentacion,
    -- actualizamos la tabla catalogo para que coincida.
    UPDATE catalogo c
    JOIN vehiculo v ON c.placa = v.placa
    SET c.fecha_publicacion = NEW.fecha_ingreso
    WHERE v.cod_documento = NEW.cod_documento;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `historia_estado_vehiculo`
--

CREATE TABLE `historia_estado_vehiculo` (
  `cod_historia` int(11) NOT NULL,
  `placa` varchar(20) NOT NULL,
  `estado` varchar(50) DEFAULT NULL,
  `fecha_cambio` datetime DEFAULT current_timestamp(),
  `observaciones` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `historia_estado_vehiculo`
--

INSERT INTO `historia_estado_vehiculo` (`cod_historia`, `placa`, `estado`, `fecha_cambio`, `observaciones`) VALUES
(1, 'ksokqw28', 'Disponible', '2026-07-07 18:22:52', 'Ingreso inicial del vehículo al sistema.'),
(3, 'YUHH544', 'Disponible', '2026-07-08 16:27:48', 'Cambio automático desde servicios: Mantenimiento -> Disponible'),
(4, 'YUHH544', 'Servicio', '2026-07-08 16:28:09', 'Cambio automático desde servicios: Disponible -> Servicio'),
(5, 'YUHH544', 'Disponible', '2026-07-08 16:29:37', 'Cambio automático desde servicios: Servicio -> Disponible'),
(6, 'FJA-KSK', 'Disponible', '2026-08-31 17:42:51', 'Ingreso inicial al sistema.'),
(7, 'FJA-KSK', 'Disponible', '2026-08-31 17:44:03', 'Actualización de datos manual.'),
(8, 'FJA-KSK', 'Disponible', '2026-08-31 21:30:09', 'Actualización de datos manual.'),
(9, 'YUY66767', 'Disponible', '2026-08-31 21:46:07', 'Ingreso inicial al sistema.'),
(10, 'YUY66767', 'Disponible', '2026-09-11 11:56:37', 'Actualización de datos manual.'),
(11, 'ksokqw28', 'Vendido', '2026-09-11 12:31:09', 'Modificaciones de los servicios: Disponible -> Vendido'),
(12, 'YUY66767', 'Vendido', '2026-09-11 13:58:55', 'Modificaciones de los servicios: Disponible -> Vendido'),
(13, 'YUY66767', 'Vendido', '2026-09-11 13:58:55', 'Actualización de datos manual.'),
(14, 'YUY66767', 'Vendido', '2026-09-11 14:09:39', 'Actualización de datos manual.'),
(15, 'YUY66767', 'Disponible', '2026-09-11 14:10:09', 'Modificaciones de los servicios: Vendido -> Disponible'),
(16, 'YUY66767', 'Disponible', '2026-09-11 14:10:09', 'Actualización de datos manual.'),
(17, 'YUY66767', 'Vendido', '2026-09-11 14:19:28', 'Modificaciones de los servicios: Disponible -> Vendido'),
(18, 'YUY66767', 'Vendido', '2026-09-11 14:19:28', 'Actualización de datos manual.'),
(19, 'YUY66767', 'Disponible', '2026-09-11 14:20:31', 'Modificaciones de los servicios: Vendido -> Disponible'),
(20, 'YUY66767', 'Disponible', '2026-09-11 14:20:31', 'Actualización de datos manual.'),
(21, 'YUHH544', 'Mantenimiento', '2026-09-11 23:00:30', 'Modificaciones de los servicios: Disponible -> Mantenimiento'),
(22, 'YUY66767', 'Disponible', '2026-09-12 21:08:47', 'Actualización de datos manual.'),
(23, 'YUHH544', 'Disponible', '2026-09-12 21:20:02', 'Modificaciones de los servicios: Mantenimiento -> Disponible'),
(24, 'YUHH544', 'Servicio', '2026-09-12 21:24:37', 'Modificaciones de los servicios: Disponible -> Servicio'),
(25, 'FJA-KSK', 'Vendido', '2026-09-12 21:41:41', 'Modificaciones de los servicios: Disponible -> Vendido'),
(26, 'YUHH544', 'Disponible', '2026-09-12 21:42:12', 'Modificaciones de los servicios: Servicio -> Disponible'),
(27, 'YUY66767', 'Vendido', '2026-09-12 21:44:28', 'Modificaciones de los servicios: Disponible -> Vendido'),
(28, 'YUHH544', 'Vendido', '2026-09-12 22:48:30', 'Modificaciones de los servicios: Disponible -> Vendido'),
(29, 'YUHH544', 'Disponible', '2026-09-12 22:52:18', 'Modificaciones de los servicios: Vendido -> Disponible'),
(30, 'ksokqw28', 'Disponible', '2026-09-12 22:52:53', 'Modificaciones de los servicios: Vendido -> Disponible'),
(31, 'YUHH544', 'Vendido', '2026-09-12 22:58:23', 'Modificaciones de los servicios: Disponible -> Vendido'),
(32, 'YUHH544', 'Disponible', '2026-09-12 23:02:11', 'Modificaciones de los servicios: Vendido -> Disponible'),
(33, 'ksokqw28', 'Vendido', '2026-09-12 23:03:08', 'Modificaciones de los servicios: Disponible -> Vendido'),
(34, 'YUHH544', 'Vendido', '2026-09-12 23:11:45', 'Modificaciones de los servicios: Disponible -> Vendido'),
(35, 'EF345GH', 'Vendido', '2026-09-13 00:23:11', 'Modificaciones de los servicios: Disponible -> Vendido'),
(36, 'EF345GH', 'Disponible', '2026-09-13 00:54:46', 'Modificaciones de los servicios: Vendido -> Disponible'),
(37, 'AB012CD', 'Vendido', '2026-09-14 00:23:50', 'Modificaciones de los servicios: Disponible -> Vendido'),
(38, 'YUY66767', 'Disponible', '2026-09-16 12:16:06', 'Modificaciones de los servicios: Vendido -> Disponible'),
(39, 'AB123CD', 'Vendido', '2026-09-17 12:39:01', 'Modificaciones de los servicios: Disponible -> Vendido'),
(40, 'CD234EF', 'Vendido', '2026-09-17 13:12:51', 'Modificaciones de los servicios: Disponible -> Vendido'),
(41, 'EF345GH', 'Vendido', '2026-09-17 13:35:05', 'Modificaciones de los servicios: Disponible -> Vendido'),
(42, 'EF456GH', 'Vendido', '2026-10-20 21:44:55', 'Modificaciones de los servicios: Disponible -> Vendido'),
(43, 'IJ789KL', 'Vendido', '2026-11-22 22:23:55', 'Modificaciones de los servicios: Disponible -> Vendido'),
(44, 'YUHH544', 'Disponible', '2026-11-24 16:41:18', 'Modificaciones de los servicios: Vendido -> Disponible'),
(45, 'IJ678KL', 'Mantenimiento', '2026-11-24 16:57:50', 'Modificaciones de los servicios: Disponible -> Mantenimiento');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `imagen`
--

CREATE TABLE `imagen` (
  `cod_imagen` int(11) NOT NULL,
  `URL` varchar(300) NOT NULL,
  `fecha_subida` date NOT NULL,
  `placa` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `imagen`
--

INSERT INTO `imagen` (`cod_imagen`, `URL`, `fecha_subida`, `placa`) VALUES
(5, 'uploads/coche-aislado-negro_23-2151852894.avif', '0000-00-00', 'YUHH544'),
(6, 'uploads/subaru.jpg', '0000-00-00', 'ksokqw28'),
(7, 'uploads/Changan-lider-marcas-emergentes.jpg', '0000-00-00', 'FJA-KSK'),
(8, 'uploads/images.jpg', '0000-00-00', 'YUY66767'),
(30, 'uploads/coche-aislado-negro_23-2151852894.avif', '2026-09-12', 'AB123CD'),
(31, 'uploads/subaru.jpg', '2026-09-12', 'EF456GH'),
(32, 'uploads/Changan-lider-marcas-emergentes.jpg', '2026-09-12', 'IJ789KL'),
(33, 'uploads/images.jpg', '2026-09-12', 'MN012OP'),
(34, 'uploads/coche-aislado-negro_23-2151852894.avif', '2026-09-12', 'QR345ST'),
(35, 'uploads/subaru.jpg', '2026-09-12', 'UV678WX'),
(36, 'uploads/Changan-lider-marcas-emergentes.jpg', '2026-09-12', 'YZ901AB'),
(37, 'uploads/images.jpg', '2026-09-12', 'CD234EF'),
(38, 'uploads/coche-aislado-negro_23-2151852894.avif', '2026-09-12', 'GH567IJ'),
(39, 'uploads/subaru.jpg', '2026-09-12', 'KL890MN'),
(40, 'uploads/Changan-lider-marcas-emergentes.jpg', '2026-09-12', 'OP123QR'),
(41, 'uploads/images.jpg', '2026-09-12', 'ST456UV'),
(42, 'uploads/coche-aislado-negro_23-2151852894.avif', '2026-09-12', 'WX789YZ'),
(43, 'uploads/subaru.jpg', '2026-09-12', 'AB012CD'),
(44, 'uploads/Changan-lider-marcas-emergentes.jpg', '2026-09-12', 'EF345GH'),
(45, 'uploads/images.jpg', '2026-09-12', 'IJ678KL'),
(46, 'uploads/coche-aislado-negro_23-2151852894.avif', '2026-09-12', 'MN901OP'),
(47, 'uploads/subaru.jpg', '2026-09-12', 'QR234ST'),
(48, 'uploads/Changan-lider-marcas-emergentes.jpg', '2026-09-12', 'UV567WX'),
(49, 'uploads/images.jpg', '2026-09-12', 'YZ890AB');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `insumos`
--

CREATE TABLE `insumos` (
  `cod_insumo` int(11) NOT NULL,
  `nombre_insumo` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `stock` int(11) DEFAULT 0,
  `unidad_medida` varchar(20) NOT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT 1,
  `fecha_registro` date NOT NULL,
  `precio_unitario` decimal(12,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `insumos`
--

INSERT INTO `insumos` (`cod_insumo`, `nombre_insumo`, `descripcion`, `stock`, `unidad_medida`, `estado`, `fecha_registro`, `precio_unitario`) VALUES
(2, 'aceite', 'hjfgjhfhj', 20, '', 1, '0000-00-00', 0.00),
(3, 'jabon', 'porque hay que limpiar', 8, '', 1, '0000-00-00', 0.00),
(4, 'filtro', '', 9, '', 1, '0000-00-00', 0.00),
(5, 'caucho', '', 6, '', 1, '0000-00-00', 0.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mantenimiento`
--

CREATE TABLE `mantenimiento` (
  `cod_mantenimiento` int(11) NOT NULL,
  `descripcion_general` text DEFAULT NULL,
  `costo_base` decimal(10,2) DEFAULT NULL,
  `costo_final` decimal(10,2) DEFAULT NULL,
  `quien_autoriza` varchar(30) NOT NULL,
  `estado` varchar(20) DEFAULT 'Pendiente'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `mantenimiento`
--

INSERT INTO `mantenimiento` (`cod_mantenimiento`, `descripcion_general`, `costo_base`, `costo_final`, `quien_autoriza`, `estado`) VALUES
(1, 'asasassasas', NULL, 20.00, '29880513', 'Finalizado'),
(2, 'urfytytfytfyty', 20.00, 50.00, '18998754', 'Finalizado'),
(3, 'le falta cosas', NULL, NULL, '18998754', 'Activo');

--
-- Disparadores `mantenimiento`
--
DELIMITER $$
CREATE TRIGGER `trg_mantenimiento_inactivo_vehiculo_disponible` AFTER UPDATE ON `mantenimiento` FOR EACH ROW BEGIN
   
    IF OLD.estado <> 'Inactivo' AND NEW.estado = 'Inactivo' THEN

        UPDATE vehiculo AS v
        INNER JOIN det_mantenimiento AS dm
            ON dm.placa = v.placa
        SET v.estado = 'Disponible'
        WHERE dm.cod_mantenimiento = NEW.cod_mantenimiento;

    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mantenimiento_cant`
--

CREATE TABLE `mantenimiento_cant` (
  `cod_detalle_mant` int(11) NOT NULL,
  `cod_mantenimiento` int(11) NOT NULL,
  `descripcion_detalle` varchar(250) DEFAULT NULL,
  `cantidad` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `marca`
--

CREATE TABLE `marca` (
  `cod_marca` int(11) NOT NULL,
  `nombre_marca` varchar(50) NOT NULL,
  `estado` varchar(20) DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `marca`
--

INSERT INTO `marca` (`cod_marca`, `nombre_marca`, `estado`) VALUES
(1, 'Volswaguen', 'Activo'),
(2, 'Toyota', 'Activo'),
(3, 'Holaa', 'Inactivo'),
(4, 'yujuu', 'Activo'),
(5, 'Hola', 'Inactivo'),
(6, 'Holaa', 'Activo');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `metodo_pago`
--

CREATE TABLE `metodo_pago` (
  `cod_metodo` int(11) NOT NULL,
  `nombre_metodo` varchar(50) NOT NULL,
  `requiere_referencia` tinyint(1) NOT NULL,
  `estado` varchar(20) DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `metodo_pago`
--

INSERT INTO `metodo_pago` (`cod_metodo`, `nombre_metodo`, `requiere_referencia`, `estado`) VALUES
(1, 'Binance', 0, 'Activo'),
(2, 'Efectivo', 0, 'Activo'),
(3, 'Pago Móvil', 1, 'Activo'),
(4, 'Zelle', 1, 'Activo'),
(5, 'Transferencia Bancaria', 1, 'Activo'),
(6, 'Zinli', 1, 'Activo'),
(7, 'YENES', 1, 'Inactivo');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `modelo`
--

CREATE TABLE `modelo` (
  `cod_modelo` int(11) NOT NULL,
  `nombre_modelo` varchar(50) NOT NULL,
  `estado` varchar(20) DEFAULT 'Activo',
  `cod_marca` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `modelo`
--

INSERT INTO `modelo` (`cod_modelo`, `nombre_modelo`, `estado`, `cod_marca`) VALUES
(1, 'Hilux', 'Activo', 1),
(2, 'Hondra', 'Activo', 2),
(3, 'Corolla', 'Activo', 1),
(4, 'Corolla', 'Inactivo', 1),
(5, 'hilux', 'Activo', 2),
(6, 'hilux', 'Activo', 6);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `moneda`
--

CREATE TABLE `moneda` (
  `cod_moneda` int(11) NOT NULL,
  `nombre_moneda` varchar(50) NOT NULL,
  `simbolo` varchar(10) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `moneda`
--

INSERT INTO `moneda` (`cod_moneda`, `nombre_moneda`, `simbolo`, `estado`) VALUES
(1, 'Dólar', '$', 'Activo'),
(2, 'Bolívar', 'Bs.', 'Activo'),
(3, 'Euro', '€', 'Activo');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `moneda_digital`
--

CREATE TABLE `moneda_digital` (
  `cod_mon_digital` int(11) NOT NULL,
  `nombre_digital` varchar(50) NOT NULL,
  `simbolo_digital` varchar(30) DEFAULT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `moneda_digital`
--

INSERT INTO `moneda_digital` (`cod_mon_digital`, `nombre_digital`, `simbolo_digital`, `estado`) VALUES
(1, 'Dolar USDT', '$', 1),
(2, 'Dolar Zelle', '$', 1),
(3, 'Dolar Zinli', '$', 1),
(4, 'Tether USD', 'USDT', 0);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pago_cuentas`
--

CREATE TABLE `pago_cuentas` (
  `cod_pagos` int(11) NOT NULL,
  `monto_abonado` decimal(15,2) DEFAULT NULL,
  `fecha_pago` datetime NOT NULL,
  `referencia` varchar(255) DEFAULT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'Procesado',
  `cod_cuentas` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pago_cuentas`
--

INSERT INTO `pago_cuentas` (`cod_pagos`, `monto_abonado`, `fecha_pago`, `referencia`, `estado`, `cod_cuentas`) VALUES
(1, 5000.00, '2026-09-11 12:31:09', '3433444', 'Procesado', 1),
(2, 50000.00, '2026-09-12 21:41:41', '1235454', 'Procesado', 2),
(3, 20000.00, '2026-09-12 21:44:28', '2121212', 'Procesado', 3),
(4, 5000.00, '2026-09-12 22:48:30', '', 'Anulado', 4),
(5, 5000.00, '2026-09-12 22:58:23', '1345445646', 'Anulado', 5),
(6, 5000.00, '2026-09-12 23:03:08', '12345688888', 'Procesado', 6),
(7, 5000.00, '2026-09-12 23:11:45', '154896456', 'Procesado', 7),
(8, 10000.00, '2026-09-13 00:23:11', '', 'Anulado', 8),
(9, 14500.00, '2026-09-14 00:23:50', '1213245315', 'Procesado', 9),
(10, 1200.00, '2026-09-15 22:12:44', '12345SA6D4S5A64D5A', 'Procesado', 3),
(11, 3100.00, '2026-09-15 22:47:34', 'DA1D2A31D5S6A', 'Anulado', 3),
(12, 1850.00, '2026-09-17 12:39:01', '', 'Procesado', 10),
(13, 4130.07, '2026-09-17 12:40:42', NULL, 'Procesado', 10),
(14, 5900.09, '2026-09-17 13:12:51', '', 'Procesado', 11),
(15, 5310.08, '2026-09-17 13:35:05', '12345688888', 'Procesado', 12),
(16, 4200.00, '2026-09-17 13:44:33', 'F245645FDS45GD4G6DG4', 'Procesado', 10),
(17, 15000.00, '2026-10-20 21:44:55', '', 'Procesado', 13),
(18, 1100.00, '2026-11-22 22:23:55', '', 'Procesado', 14),
(19, 990.00, '2026-11-22 23:28:40', '123459887897899', 'Procesado', 14),
(20, 990.00, '2026-11-24 16:44:48', '54545454', 'Procesado', 14);

--
-- Disparadores `pago_cuentas`
--
DELIMITER $$
CREATE TRIGGER `trg_after_update_pago_anulado` AFTER UPDATE ON `pago_cuentas` FOR EACH ROW BEGIN
    IF OLD.estado <> 'Anulado' AND NEW.estado = 'Anulado' THEN
        UPDATE cuotas c
        INNER JOIN pago_cuota_detalle pcd ON c.cod_cuota = pcd.cod_cuota
        SET c.monto_pagado = GREATEST(0.00, c.monto_pagado - pcd.monto_aplicado),
            c.estado = CASE
                WHEN GREATEST(0.00, c.monto_pagado - pcd.monto_aplicado) >= c.monto_cuota THEN 'Pagada'
                WHEN GREATEST(0.00, c.monto_pagado - pcd.monto_aplicado) > 0 THEN 'Parcial'
                WHEN c.fecha_vencimiento < CURDATE() THEN 'Vencida'
                ELSE 'Pendiente'
            END,
            c.fecha_pago = CASE
                WHEN GREATEST(0.00, c.monto_pagado - pcd.monto_aplicado) >= c.monto_cuota THEN c.fecha_pago
                ELSE NULL
            END
        WHERE pcd.cod_pagos = NEW.cod_pagos;
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pago_cuota_detalle`
--

CREATE TABLE `pago_cuota_detalle` (
  `cod_pago_cuota` int(11) NOT NULL,
  `cod_pagos` int(11) NOT NULL,
  `cod_cuota` int(11) NOT NULL,
  `monto_aplicado` decimal(15,2) NOT NULL,
  `fecha_aplicacion` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pago_cuota_detalle`
--

INSERT INTO `pago_cuota_detalle` (`cod_pago_cuota`, `cod_pagos`, `cod_cuota`, `monto_aplicado`, `fecha_aplicacion`) VALUES
(1, 19, 1, 990.00, '2026-11-22 23:28:40'),
(2, 20, 2, 990.00, '2026-11-24 16:44:48');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `propietario`
--

CREATE TABLE `propietario` (
  `cedula_propietario` int(11) NOT NULL,
  `razon_social` varchar(100) NOT NULL,
  `telefono` varchar(20) NOT NULL,
  `correo` varchar(50) DEFAULT NULL,
  `direccion` varchar(250) DEFAULT NULL,
  `tipo` varchar(50) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'Activo',
  `fecha_registro` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `propietario`
--

INSERT INTO `propietario` (`cedula_propietario`, `razon_social`, `telefono`, `correo`, `direccion`, `tipo`, `estado`, `fecha_registro`) VALUES
(12345678, 'Yessica Lopez', '04162006154', 'yessi@gmail.com', 'el roble', 'Empresa', 'Inactivo', '2026-08-31'),
(14094670, 'Yenifer Escobar', '04125273638', 'yenifer@gmail.com', 'jose feliiix', 'Natural', 'Activo', '2026-07-07'),
(15663645, 'Yessica Lopez', '04162006154', 'hola@gmail.com', 'roblee', 'Empresa', 'Inactivo', '2026-08-31'),
(28123456, 'Alberto Perez', '04125558744', 'alberto@mail.com', 'Cabudare agua viva', 'Dueño', 'Activo', NULL),
(29880513, 'Daryeli Gutierrez', '04141593342', 'tuku@gmial.com', 'villa productiva', 'Natural', 'Activo', '2026-07-07');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `proveedor_compra`
--

CREATE TABLE `proveedor_compra` (
  `rif_cedula_proveedor` int(11) NOT NULL,
  `razon_social` varchar(250) NOT NULL,
  `direccion` text NOT NULL,
  `telefono` int(20) NOT NULL,
  `correo` varchar(50) NOT NULL,
  `estado` varchar(20) DEFAULT 'Activo',
  `fecha_registro` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `proveedor_compra`
--

INSERT INTO `proveedor_compra` (`rif_cedula_proveedor`, `razon_social`, `direccion`, `telefono`, `correo`, `estado`, `fecha_registro`) VALUES
(2424242, 'Daryeli Gutierrez', 'dfdava', 2147483647, 'tuku@gmial.com', 'Activo', '2026-09-11'),
(23685946, 'Yessica Lopez', 'tu cora', 422556879, 'yessi@gmail.com', 'Activo', '2026-09-11');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `servicios`
--

CREATE TABLE `servicios` (
  `cod_servicios` int(11) NOT NULL,
  `nombre_servicio` varchar(100) DEFAULT NULL,
  `costo_base` decimal(10,2) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `servicios`
--

INSERT INTO `servicios` (`cod_servicios`, `nombre_servicio`, `costo_base`, `estado`) VALUES
(1, 'limpieza', 50.00, 'Finalizado'),
(2, 'limpieza', 20.00, 'Finalizado');

--
-- Disparadores `servicios`
--
DELIMITER $$
CREATE TRIGGER `trg_servicio_inactivo_vehiculo_disponible` AFTER UPDATE ON `servicios` FOR EACH ROW BEGIN
    
    IF OLD.estado <> 'Inactivo' AND NEW.estado = 'Inactivo' THEN

        UPDATE vehiculo AS v
        INNER JOIN det_servicios AS ds
            ON ds.placa = v.placa
        SET v.estado = 'Disponible'
        WHERE ds.cod_servicios = NEW.cod_servicios
          AND v.estado = 'Servicio';

    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `taller`
--

CREATE TABLE `taller` (
  `cod_taller` int(11) NOT NULL,
  `nombre_taller` varchar(100) NOT NULL,
  `direccion` varchar(250) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `taller`
--

INSERT INTO `taller` (`cod_taller`, `nombre_taller`, `direccion`, `estado`) VALUES
(1, 'Centroo', 'av 20', '1'),
(2, 'Alan calito', 'calle 39 con 23 y 24', '1');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tasa_cambio`
--

CREATE TABLE `tasa_cambio` (
  `id` int(11) NOT NULL,
  `valor` decimal(10,4) NOT NULL,
  `fecha` date NOT NULL,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tasa_cambio`
--

INSERT INTO `tasa_cambio` (`id`, `valor`, `fecha`, `creado_en`) VALUES
(1, 596.7824, '2026-06-17', '2026-06-17 05:14:45'),
(2, 607.3919, '2026-06-20', '2026-06-21 03:23:14'),
(3, 617.6388, '2026-06-23', '2026-06-24 02:56:24'),
(4, 617.6388, '2026-06-24', '2026-06-24 04:05:01'),
(5, 639.7029, '2026-07-02', '2026-07-02 05:31:42'),
(6, 685.9427, '2026-07-08', '2026-07-08 19:05:11'),
(7, 832.4883, '2026-09-12', '2026-09-13 01:40:13'),
(8, 832.4883, '2026-09-13', '2026-09-13 04:22:40'),
(9, 832.4883, '2026-09-14', '2026-09-14 04:23:29'),
(10, 842.2067, '2026-09-15', '2026-09-16 02:12:05'),
(11, 846.5131, '2026-09-16', '2026-09-16 15:37:43'),
(12, 847.4442, '2026-09-17', '2026-09-17 16:25:56'),
(13, 855.6625, '2026-09-26', '2026-09-26 23:36:46'),
(14, 875.6505, '2026-10-11', '2026-10-12 01:19:40'),
(15, 880.1159, '2026-10-17', '2026-10-18 02:24:50'),
(16, 881.8769, '2026-10-20', '2026-10-21 00:50:17'),
(17, 918.7662, '2026-11-22', '2026-11-23 02:21:22'),
(18, 919.8227, '2026-11-24', '2026-11-24 17:22:52');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tipo_vehiculo`
--

CREATE TABLE `tipo_vehiculo` (
  `cod_tipo` int(11) NOT NULL,
  `nombre_tipo` varchar(50) NOT NULL,
  `descripcion` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tipo_vehiculo`
--

INSERT INTO `tipo_vehiculo` (`cod_tipo`, `nombre_tipo`, `descripcion`) VALUES
(1, 'Sedan', NULL),
(2, 'Pick-up', NULL),
(3, 'Coupe', NULL),
(4, 'Suv', NULL),
(5, 'Moto', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `vehiculo`
--

CREATE TABLE `vehiculo` (
  `placa` varchar(20) NOT NULL,
  `color` varchar(50) NOT NULL,
  `anio` int(11) NOT NULL,
  `kilometraje` int(20) NOT NULL,
  `estado` varchar(20) DEFAULT 'Disponible',
  `cod_tipo` int(11) NOT NULL,
  `cod_modelo` int(11) NOT NULL,
  `cod_documento` int(11) NOT NULL,
  `cod_accesorio` int(11) NOT NULL,
  `cedula_propietario` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `vehiculo`
--

INSERT INTO `vehiculo` (`placa`, `color`, `anio`, `kilometraje`, `estado`, `cod_tipo`, `cod_modelo`, `cod_documento`, `cod_accesorio`, `cedula_propietario`) VALUES
('AB012CD', 'Dorado', 2022, 27000, 'Vendido', 2, 4, 43, 43, 29880513),
('AB123CD', 'Negro', 2020, 45000, 'Vendido', 1, 1, 30, 30, 14094670),
('CD234EF', 'Amarillo', 2021, 40000, 'Vendido', 1, 3, 37, 37, 29880513),
('EF345GH', 'Vino', 2020, 48000, 'Vendido', 5, 5, 44, 44, 14094670),
('EF456GH', 'Blanco', 2021, 32000, 'Vendido', 2, 2, 31, 31, 29880513),
('FJA-KSK', 'Negro', 2000, 50000, 'Vendido', 1, 3, 12, 12, 28123456),
('GH567IJ', 'Naranja', 2022, 22000, 'Disponible', 4, 4, 38, 38, 14094670),
('IJ678KL', 'Beige', 2023, 12000, 'Mantenimiento', 1, 1, 45, 45, 28123456),
('IJ789KL', 'Rojo', 2019, 68000, 'Vendido', 1, 3, 32, 32, 14094670),
('KL890MN', 'Morado', 2020, 60000, 'Disponible', 2, 5, 39, 39, 28123456),
('ksokqw28', 'blanco', 2020, 60000, 'Vendido', 2, 2, 11, 11, 28123456),
('MN012OP', 'Azul', 2022, 15000, 'Disponible', 4, 5, 33, 33, 28123456),
('MN901OP', 'Turquesa', 2021, 33000, 'Disponible', 3, 2, 46, 46, 29880513),
('OP123QR', 'Rosado', 2023, 5000, 'Disponible', 3, 1, 40, 40, 29880513),
('QR234ST', 'Coral', 2019, 80000, 'Disponible', 4, 3, 47, 47, 14094670),
('QR345ST', 'Gris', 2020, 55000, 'Disponible', 2, 1, 34, 34, 29880513),
('ST456UV', 'Cyan', 2021, 38000, 'Disponible', 1, 2, 41, 41, 14094670),
('UV567WX', 'Lila', 2022, 18000, 'Disponible', 2, 4, 48, 48, 28123456),
('UV678WX', 'Plateado', 2023, 8000, 'Disponible', 3, 2, 35, 35, 14094670),
('WX789YZ', 'Marrón', 2019, 72000, 'Disponible', 4, 3, 42, 42, 28123456),
('YUHH544', 'Negro', 2025, 3000, 'Disponible', 1, 2, 10, 10, 29880513),
('YUY66767', 'Rojo', 2020, 30000, 'Disponible', 2, 2, 14, 14, 14094670),
('YZ890AB', 'Champagne', 2023, 3000, 'Disponible', 1, 5, 49, 49, 29880513),
('YZ901AB', 'Verde', 2018, 95000, 'Disponible', 5, 1, 36, 36, 28123456);

--
-- Disparadores `vehiculo`
--
DELIMITER $$
CREATE TRIGGER `trg_historial_estado_vehiculo_servicios` AFTER UPDATE ON `vehiculo` FOR EACH ROW BEGIN
    IF NEW.estado <> OLD.estado THEN
        INSERT INTO historia_estado_vehiculo (placa, estado, fecha_cambio, observaciones)
        VALUES (
            NEW.placa,
            NEW.estado,
            NOW(),
            CONCAT('Modificaciones de los servicios: ', OLD.estado, ' -> ', NEW.estado)
        );
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ventas`
--

CREATE TABLE `ventas` (
  `cod_venta` int(11) NOT NULL,
  `estado` varchar(20) DEFAULT 'Pendiente',
  `fecha_venta` date NOT NULL,
  `tipo_venta` varchar(45) DEFAULT NULL,
  `cedula_usuario` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `ventas`
--

INSERT INTO `ventas` (`cod_venta`, `estado`, `fecha_venta`, `tipo_venta`, `cedula_usuario`) VALUES
(1, 'Anulada', '2026-09-11', 'contado', '29880513'),
(2, 'procesada', '2026-09-12', 'contado', '29880513'),
(3, 'Anulada', '2026-09-12', 'credito', '29880513'),
(4, 'Anulada', '2026-09-12', 'contado', '29880513'),
(5, 'Anulada', '2026-09-12', 'contado', '29880513'),
(6, 'procesada', '2026-09-12', 'contado', '29880513'),
(7, 'procesada', '2026-09-12', 'contado', '29880513'),
(8, 'Anulada', '2026-09-13', 'contado', '29880513'),
(9, 'procesada', '2026-09-14', 'contado', '29880513'),
(10, 'procesada', '2026-09-17', 'credito', '29880513'),
(11, 'procesada', '2026-09-17', 'credito', '29880513'),
(12, 'procesada', '2026-09-17', 'credito', '29880513'),
(13, 'procesada', '2026-10-20', 'contado', '7423045'),
(14, 'procesada', '2026-11-22', 'credito', '14094670');

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_cuotas_detalladas`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_cuotas_detalladas` (
`cod_cuota` int(11)
,`cod_cuentas` int(11)
,`numero_cuota` int(11)
,`monto_cuota` decimal(15,2)
,`monto_pagado` decimal(15,2)
,`saldo_cuota` decimal(16,2)
,`fecha_vencimiento` date
,`fecha_pago` datetime
,`estado_guardado` varchar(20)
,`estado_actual` varchar(20)
,`dias_mora` int(7)
,`observaciones` varchar(255)
,`frecuencia_pago` varchar(20)
,`cantidad_cuotas` int(11)
,`deuda_total` decimal(15,2)
,`deuda_cuenta` decimal(15,2)
,`cod_venta` int(11)
,`fecha_venta` date
,`cedula_usuario` varchar(20)
,`nombre_cliente` varchar(146)
,`telefono_cliente` varchar(20)
,`placa` varchar(20)
,`nombre_marca` varchar(50)
,`nombre_modelo` varchar(50)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_detalle_pagos`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_detalle_pagos` (
`cod_venta` int(11)
,`cliente` varchar(20)
,`cod_cuentas` int(11)
,`deuda_original` decimal(15,2)
,`cod_pagos` int(11)
,`monto_abonado` decimal(15,2)
,`fecha_pago` datetime
,`tipo_pago` varchar(20)
,`referencia_transaccion` varchar(255)
,`monto_detalle` decimal(12,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_mantenimientos_detallados`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_mantenimientos_detallados` (
`cod_mantenimiento` int(11)
,`descripcion_general` text
,`quien_autoriza` varchar(30)
,`estado_mantenimiento` varchar(20)
,`cod_detalle` int(11)
,`tipo` varchar(20)
,`fecha_solicitud` date
,`fecha_completada` date
,`placa` varchar(20)
,`color` varchar(50)
,`anio` int(11)
,`kilometraje` int(20)
,`estado_vehiculo` varchar(20)
,`cod_taller` int(11)
,`nombre_taller` varchar(100)
,`direccion_taller` varchar(250)
,`estado_taller` varchar(20)
,`cedula_usuario` varchar(20)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_propietarios_resumen`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_propietarios_resumen` (
`cedula_propietario` int(11)
,`razon_social` varchar(100)
,`telefono` varchar(20)
,`correo` varchar(50)
,`direccion` varchar(250)
,`tipo` varchar(50)
,`estado` varchar(20)
,`fecha_registro` date
,`cantidad_vehiculos` bigint(21)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_resumen_clientes`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_resumen_clientes` (
`cedula_usuario` varchar(20)
,`cantidad_compras` bigint(21)
,`monto_total_financiado` decimal(37,2)
,`deuda_actual_pendiente` decimal(37,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_resumen_creditos_cuotas`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_resumen_creditos_cuotas` (
`cod_cuentas` int(11)
,`cod_venta` int(11)
,`deuda_total` decimal(15,2)
,`monto_inicial` decimal(15,2)
,`tasa_interes` decimal(5,2)
,`deuda` decimal(15,2)
,`frecuencia_pago` varchar(20)
,`cantidad_cuotas` int(11)
,`fecha_emision` date
,`fecha_inicio_cuotas` date
,`fecha_vencimiento_final` datetime
,`estado_cuenta` varchar(20)
,`total_cuotas_generadas` bigint(21)
,`cuotas_pagadas` decimal(22,0)
,`cuotas_pendientes` decimal(22,0)
,`cuotas_vencidas` decimal(22,0)
,`proxima_fecha_vencimiento` date
,`monto_vencido` decimal(38,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_servicios_detallados`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_servicios_detallados` (
`cod_servicios` int(11)
,`nombre_servicio` varchar(100)
,`costo_base` decimal(10,2)
,`estado` varchar(20)
,`cod_det_servicio` int(11)
,`costo_final` decimal(10,2)
,`descripcion_especifica` varchar(250)
,`fecha_realizacion` date
,`placa` varchar(20)
,`estado_vehiculo` varchar(20)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_vehiculos_propietarios_detalle`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_vehiculos_propietarios_detalle` (
`cedula_propietario` int(11)
,`placa` varchar(20)
,`nombre_marca` varchar(50)
,`nombre_modelo` varchar(50)
,`anio` int(11)
,`color` varchar(50)
,`estado` varchar(20)
,`precio` decimal(10,2)
,`imagen_url` varchar(300)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_citas_detalle`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_citas_detalle` (
`cod_citas` int(11)
,`fecha` date
,`hora` time
,`estado` varchar(20)
,`activo` int(1)
,`cod_catalogo` int(11)
,`precio` decimal(10,2)
,`placa` varchar(20)
,`nombre_marca` varchar(50)
,`nombre_modelo` varchar(50)
,`cedula_usuario` varchar(20)
,`nombre_cliente` varchar(45)
,`apellido_cliente` varchar(100)
,`telefono_cliente` varchar(20)
,`correo_cliente` varchar(50)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_clientes_activos`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_clientes_activos` (
`cedula_usuario` varchar(20)
,`nombre` varchar(45)
,`apellido` varchar(100)
,`telefono` varchar(20)
,`direccion` text
,`correo` varchar(50)
,`foto` varchar(255)
,`nombre_rol` varchar(50)
);

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_cuotas_detalladas`
--
DROP TABLE IF EXISTS `vw_cuotas_detalladas`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_cuotas_detalladas`  AS SELECT `c`.`cod_cuota` AS `cod_cuota`, `c`.`cod_cuentas` AS `cod_cuentas`, `c`.`numero_cuota` AS `numero_cuota`, `c`.`monto_cuota` AS `monto_cuota`, `c`.`monto_pagado` AS `monto_pagado`, greatest(0.00,`c`.`monto_cuota` - `c`.`monto_pagado`) AS `saldo_cuota`, `c`.`fecha_vencimiento` AS `fecha_vencimiento`, `c`.`fecha_pago` AS `fecha_pago`, `c`.`estado` AS `estado_guardado`, CASE WHEN `c`.`estado` in ('Pendiente','Parcial') AND `c`.`fecha_vencimiento` < curdate() THEN 'Vencida' ELSE `c`.`estado` END AS `estado_actual`, CASE WHEN `c`.`estado` in ('Pendiente','Parcial','Vencida') AND `c`.`fecha_vencimiento` < curdate() THEN to_days(curdate()) - to_days(`c`.`fecha_vencimiento`) ELSE 0 END AS `dias_mora`, `c`.`observaciones` AS `observaciones`, `cxc`.`frecuencia_pago` AS `frecuencia_pago`, `cxc`.`cantidad_cuotas` AS `cantidad_cuotas`, `cxc`.`deuda_total` AS `deuda_total`, `cxc`.`deuda` AS `deuda_cuenta`, `v`.`cod_venta` AS `cod_venta`, `v`.`fecha_venta` AS `fecha_venta`, `v`.`cedula_usuario` AS `cedula_usuario`, concat(`u`.`nombre`,' ',`u`.`apellido`) AS `nombre_cliente`, `u`.`telefono` AS `telefono_cliente`, `dv`.`placa` AS `placa`, `ma`.`nombre_marca` AS `nombre_marca`, `mo`.`nombre_modelo` AS `nombre_modelo` FROM (((((((`cuotas` `c` join `cuentas_por_cobrar` `cxc` on(`c`.`cod_cuentas` = `cxc`.`cod_cuentas`)) join `ventas` `v` on(`cxc`.`cod_venta` = `v`.`cod_venta`)) left join `seguridad`.`t_usuario` `u` on(`v`.`cedula_usuario` = `u`.`cedula_usuario`)) left join `det_venta` `dv` on(`v`.`cod_venta` = `dv`.`cod_venta`)) left join `vehiculo` `veh` on(`dv`.`placa` = `veh`.`placa`)) left join `modelo` `mo` on(`veh`.`cod_modelo` = `mo`.`cod_modelo`)) left join `marca` `ma` on(`mo`.`cod_marca` = `ma`.`cod_marca`)) ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_detalle_pagos`
--
DROP TABLE IF EXISTS `vw_detalle_pagos`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_detalle_pagos`  AS SELECT `v`.`cod_venta` AS `cod_venta`, `v`.`cedula_usuario` AS `cliente`, `cxc`.`cod_cuentas` AS `cod_cuentas`, `cxc`.`deuda_total` AS `deuda_original`, `pc`.`cod_pagos` AS `cod_pagos`, `pc`.`monto_abonado` AS `monto_abonado`, `pc`.`fecha_pago` AS `fecha_pago`, `dp`.`tipo_pago` AS `tipo_pago`, coalesce(`db`.`referencia`,`dnd`.`referencia`) AS `referencia_transaccion`, coalesce(`db`.`monto`,`dnd`.`monto`) AS `monto_detalle` FROM (((((`ventas` `v` join `cuentas_por_cobrar` `cxc` on(`v`.`cod_venta` = `cxc`.`cod_venta`)) left join `pago_cuentas` `pc` on(`cxc`.`cod_cuentas` = `pc`.`cod_cuentas`)) left join `det_pago` `dp` on(`pc`.`cod_pagos` = `dp`.`cod_pagos`)) left join `det_banco` `db` on(`dp`.`cod_det_pago` = `db`.`cod_det_pago`)) left join `det_nom_digital` `dnd` on(`dp`.`cod_det_pago` = `dnd`.`cod_det_pago`)) ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_mantenimientos_detallados`
--
DROP TABLE IF EXISTS `vw_mantenimientos_detallados`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_mantenimientos_detallados`  AS SELECT `m`.`cod_mantenimiento` AS `cod_mantenimiento`, `m`.`descripcion_general` AS `descripcion_general`, `m`.`quien_autoriza` AS `quien_autoriza`, `m`.`estado` AS `estado_mantenimiento`, `dm`.`cod_detalle` AS `cod_detalle`, `dm`.`tipo` AS `tipo`, `dm`.`fecha_solicitud` AS `fecha_solicitud`, `dm`.`fecha_completada` AS `fecha_completada`, `v`.`placa` AS `placa`, `v`.`color` AS `color`, `v`.`anio` AS `anio`, `v`.`kilometraje` AS `kilometraje`, `v`.`estado` AS `estado_vehiculo`, `t`.`cod_taller` AS `cod_taller`, `t`.`nombre_taller` AS `nombre_taller`, `t`.`direccion` AS `direccion_taller`, `t`.`estado` AS `estado_taller`, `dm`.`cedula_usuario` AS `cedula_usuario` FROM (((`mantenimiento` `m` join `det_mantenimiento` `dm` on(`m`.`cod_mantenimiento` = `dm`.`cod_mantenimiento`)) join `vehiculo` `v` on(`dm`.`placa` = `v`.`placa`)) join `taller` `t` on(`dm`.`cod_taller` = `t`.`cod_taller`)) ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_propietarios_resumen`
--
DROP TABLE IF EXISTS `vw_propietarios_resumen`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_propietarios_resumen`  AS SELECT `p`.`cedula_propietario` AS `cedula_propietario`, `p`.`razon_social` AS `razon_social`, `p`.`telefono` AS `telefono`, `p`.`correo` AS `correo`, `p`.`direccion` AS `direccion`, `p`.`tipo` AS `tipo`, `p`.`estado` AS `estado`, `p`.`fecha_registro` AS `fecha_registro`, (select count(0) from `vehiculo` `v` where `v`.`cedula_propietario` = `p`.`cedula_propietario` and `v`.`estado` <> 'Inactivo') AS `cantidad_vehiculos` FROM `propietario` AS `p` WHERE `p`.`estado` <> 'Inactivo' ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_resumen_clientes`
--
DROP TABLE IF EXISTS `vw_resumen_clientes`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_resumen_clientes`  AS SELECT `v`.`cedula_usuario` AS `cedula_usuario`, count(distinct `v`.`cod_venta`) AS `cantidad_compras`, sum(`cxc`.`deuda_total`) AS `monto_total_financiado`, sum(`cxc`.`deuda`) AS `deuda_actual_pendiente` FROM (`ventas` `v` left join `cuentas_por_cobrar` `cxc` on(`v`.`cod_venta` = `cxc`.`cod_venta`)) WHERE lcase(`v`.`estado`) <> 'anulada' GROUP BY `v`.`cedula_usuario` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_resumen_creditos_cuotas`
--
DROP TABLE IF EXISTS `vw_resumen_creditos_cuotas`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_resumen_creditos_cuotas`  AS SELECT `cxc`.`cod_cuentas` AS `cod_cuentas`, `cxc`.`cod_venta` AS `cod_venta`, `cxc`.`deuda_total` AS `deuda_total`, `cxc`.`monto_inicial` AS `monto_inicial`, `cxc`.`tasa_interes` AS `tasa_interes`, `cxc`.`deuda` AS `deuda`, `cxc`.`frecuencia_pago` AS `frecuencia_pago`, `cxc`.`cantidad_cuotas` AS `cantidad_cuotas`, `cxc`.`fecha_emision` AS `fecha_emision`, `cxc`.`fecha_inicio_cuotas` AS `fecha_inicio_cuotas`, `cxc`.`fecha_vencimiento` AS `fecha_vencimiento_final`, `cxc`.`estado` AS `estado_cuenta`, count(`c`.`cod_cuota`) AS `total_cuotas_generadas`, sum(case when `c`.`estado` = 'Pagada' then 1 else 0 end) AS `cuotas_pagadas`, sum(case when `c`.`estado` in ('Pendiente','Parcial','Vencida') then 1 else 0 end) AS `cuotas_pendientes`, sum(case when `c`.`estado` in ('Pendiente','Parcial','Vencida') and `c`.`fecha_vencimiento` < curdate() then 1 else 0 end) AS `cuotas_vencidas`, min(case when `c`.`estado` in ('Pendiente','Parcial','Vencida') then `c`.`fecha_vencimiento` else NULL end) AS `proxima_fecha_vencimiento`, sum(case when `c`.`estado` in ('Pendiente','Parcial','Vencida') and `c`.`fecha_vencimiento` < curdate() then greatest(0.00,`c`.`monto_cuota` - `c`.`monto_pagado`) else 0.00 end) AS `monto_vencido` FROM (`cuentas_por_cobrar` `cxc` left join `cuotas` `c` on(`cxc`.`cod_cuentas` = `c`.`cod_cuentas`)) GROUP BY `cxc`.`cod_cuentas` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_servicios_detallados`
--
DROP TABLE IF EXISTS `vw_servicios_detallados`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_servicios_detallados`  AS SELECT `s`.`cod_servicios` AS `cod_servicios`, `s`.`nombre_servicio` AS `nombre_servicio`, `s`.`costo_base` AS `costo_base`, `s`.`estado` AS `estado`, `ds`.`cod_det_servicio` AS `cod_det_servicio`, `ds`.`costo_final` AS `costo_final`, `ds`.`descripcion_especifica` AS `descripcion_especifica`, `ds`.`fecha_realizacion` AS `fecha_realizacion`, `ds`.`placa` AS `placa`, `v`.`estado` AS `estado_vehiculo` FROM ((`servicios` `s` left join `det_servicios` `ds` on(`ds`.`cod_servicios` = `s`.`cod_servicios`)) left join `vehiculo` `v` on(`v`.`placa` = `ds`.`placa`)) ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_vehiculos_propietarios_detalle`
--
DROP TABLE IF EXISTS `vw_vehiculos_propietarios_detalle`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_vehiculos_propietarios_detalle`  AS SELECT `v`.`cedula_propietario` AS `cedula_propietario`, `v`.`placa` AS `placa`, `ma`.`nombre_marca` AS `nombre_marca`, `mo`.`nombre_modelo` AS `nombre_modelo`, `v`.`anio` AS `anio`, `v`.`color` AS `color`, `v`.`estado` AS `estado`, `c`.`precio` AS `precio`, `i`.`URL` AS `imagen_url` FROM ((((`vehiculo` `v` join `modelo` `mo` on(`v`.`cod_modelo` = `mo`.`cod_modelo`)) join `marca` `ma` on(`mo`.`cod_marca` = `ma`.`cod_marca`)) left join `catalogo` `c` on(`v`.`placa` = `c`.`placa`)) left join `imagen` `i` on(`v`.`placa` = `i`.`placa`)) WHERE `v`.`estado` <> 'Inactivo' ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_citas_detalle`
--
DROP TABLE IF EXISTS `v_citas_detalle`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_citas_detalle`  AS SELECT `c`.`cod_citas` AS `cod_citas`, `c`.`fecha` AS `fecha`, `c`.`hora` AS `hora`, `c`.`estado` AS `estado`, `c`.`activo` AS `activo`, `cat`.`cod_catalogo` AS `cod_catalogo`, `cat`.`precio` AS `precio`, `cat`.`placa` AS `placa`, `m`.`nombre_marca` AS `nombre_marca`, `mo`.`nombre_modelo` AS `nombre_modelo`, `u`.`cedula_usuario` AS `cedula_usuario`, `u`.`nombre` AS `nombre_cliente`, `u`.`apellido` AS `apellido_cliente`, `u`.`telefono` AS `telefono_cliente`, `u`.`correo` AS `correo_cliente` FROM (((((`citas` `c` join `catalogo` `cat` on(`c`.`cod_catalogo` = `cat`.`cod_catalogo`)) left join `vehiculo` `v` on(`cat`.`placa` = `v`.`placa`)) left join `modelo` `mo` on(`v`.`cod_modelo` = `mo`.`cod_modelo`)) left join `marca` `m` on(`mo`.`cod_marca` = `m`.`cod_marca`)) join `seguridad`.`t_usuario` `u` on(`c`.`cedula_usuario` = `u`.`cedula_usuario`)) ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_clientes_activos`
--
DROP TABLE IF EXISTS `v_clientes_activos`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_clientes_activos`  AS SELECT `u`.`cedula_usuario` AS `cedula_usuario`, `u`.`nombre` AS `nombre`, `u`.`apellido` AS `apellido`, `u`.`telefono` AS `telefono`, `u`.`direccion` AS `direccion`, `u`.`correo` AS `correo`, `u`.`foto` AS `foto`, `r`.`nombre_rol` AS `nombre_rol` FROM (`seguridad`.`t_usuario` `u` join `seguridad`.`t_rol` `r` on(`u`.`cod_rol` = `r`.`cod_rol`)) WHERE `u`.`cod_rol` = 4 AND `u`.`estado` = 1 ;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `accesorio`
--
ALTER TABLE `accesorio`
  ADD PRIMARY KEY (`cod_accesorio`);

--
-- Indices de la tabla `banco`
--
ALTER TABLE `banco`
  ADD PRIMARY KEY (`cod_banco`);

--
-- Indices de la tabla `catalogo`
--
ALTER TABLE `catalogo`
  ADD PRIMARY KEY (`cod_catalogo`),
  ADD KEY `fk_cat_vehiculo` (`placa`);

--
-- Indices de la tabla `citas`
--
ALTER TABLE `citas`
  ADD PRIMARY KEY (`cod_citas`),
  ADD KEY `fk_citas_cat` (`cod_catalogo`),
  ADD KEY `cedula_usuario` (`cedula_usuario`);

--
-- Indices de la tabla `compras_accesorios`
--
ALTER TABLE `compras_accesorios`
  ADD PRIMARY KEY (`cod_compras`),
  ADD KEY `rif_cedula_proveedor` (`rif_cedula_proveedor`);

--
-- Indices de la tabla `cuentas_por_cobrar`
--
ALTER TABLE `cuentas_por_cobrar`
  ADD PRIMARY KEY (`cod_cuentas`),
  ADD KEY `fk_cpc_venta` (`cod_venta`),
  ADD KEY `idx_cxc_venta` (`cod_venta`);

--
-- Indices de la tabla `cuotas`
--
ALTER TABLE `cuotas`
  ADD PRIMARY KEY (`cod_cuota`),
  ADD UNIQUE KEY `uk_cuota_cuenta_num` (`cod_cuentas`,`numero_cuota`),
  ADD KEY `idx_cuotas_estado_fecha` (`estado`,`fecha_vencimiento`);

--
-- Indices de la tabla `det_banco`
--
ALTER TABLE `det_banco`
  ADD PRIMARY KEY (`cod_det_banco`),
  ADD KEY `fk_detbanco_banco` (`cod_banco`),
  ADD KEY `fk_detbanco_pago` (`cod_det_pago`);

--
-- Indices de la tabla `det_compra`
--
ALTER TABLE `det_compra`
  ADD PRIMARY KEY (`cod_det_compra`),
  ADD UNIQUE KEY `uk_detcompra_compra_insumo` (`cod_compras`,`cod_insumo`),
  ADD KEY `fk_detcomp_insumo` (`cod_insumo`),
  ADD KEY `fk_detcomp_compra` (`cod_compras`);

--
-- Indices de la tabla `det_mantenimiento`
--
ALTER TABLE `det_mantenimiento`
  ADD PRIMARY KEY (`cod_detalle`),
  ADD KEY `fk_detmant_mant` (`cod_mantenimiento`),
  ADD KEY `fk_detmant_veh` (`placa`),
  ADD KEY `fk_detmant_taller` (`cod_taller`),
  ADD KEY `cedula_usuario` (`cedula_usuario`);

--
-- Indices de la tabla `det_nom_digital`
--
ALTER TABLE `det_nom_digital`
  ADD PRIMARY KEY (`cod_det_digital`),
  ADD KEY `fk_detdig_moneda` (`cod_mon_digital`),
  ADD KEY `fk_detdig_pago` (`cod_det_pago`);

--
-- Indices de la tabla `det_pago`
--
ALTER TABLE `det_pago`
  ADD PRIMARY KEY (`cod_det_pago`),
  ADD KEY `fk_detpago_pagocuenta` (`cod_pagos`),
  ADD KEY `fk_detpago_metodo` (`cod_metodo`),
  ADD KEY `fk_detpago_moneda` (`cod_moneda`);

--
-- Indices de la tabla `det_salida`
--
ALTER TABLE `det_salida`
  ADD PRIMARY KEY (`cod_salida`),
  ADD KEY `placa` (`placa`),
  ADD KEY `cod_insumo` (`cod_insumo`);

--
-- Indices de la tabla `det_servicios`
--
ALTER TABLE `det_servicios`
  ADD PRIMARY KEY (`cod_det_servicio`),
  ADD KEY `fk_detserv_veh` (`placa`),
  ADD KEY `fk_detserv_serv` (`cod_servicios`),
  ADD KEY `idx_det_servicios_placa` (`placa`);

--
-- Indices de la tabla `det_venta`
--
ALTER TABLE `det_venta`
  ADD PRIMARY KEY (`cod_det_venta`),
  ADD KEY `fk_detventa_veh` (`placa`),
  ADD KEY `fk_detventa_venta` (`cod_venta`);

--
-- Indices de la tabla `documentacion`
--
ALTER TABLE `documentacion`
  ADD PRIMARY KEY (`cod_documento`);

--
-- Indices de la tabla `historia_estado_vehiculo`
--
ALTER TABLE `historia_estado_vehiculo`
  ADD PRIMARY KEY (`cod_historia`),
  ADD KEY `fk_hist_vehiculo` (`placa`);

--
-- Indices de la tabla `imagen`
--
ALTER TABLE `imagen`
  ADD PRIMARY KEY (`cod_imagen`),
  ADD KEY `fk_img_vehiculo` (`placa`);

--
-- Indices de la tabla `insumos`
--
ALTER TABLE `insumos`
  ADD PRIMARY KEY (`cod_insumo`);

--
-- Indices de la tabla `mantenimiento`
--
ALTER TABLE `mantenimiento`
  ADD PRIMARY KEY (`cod_mantenimiento`),
  ADD KEY `idx_mantenimiento_estado` (`estado`);

--
-- Indices de la tabla `mantenimiento_cant`
--
ALTER TABLE `mantenimiento_cant`
  ADD PRIMARY KEY (`cod_detalle_mant`),
  ADD KEY `cod_mantenimiento` (`cod_mantenimiento`);

--
-- Indices de la tabla `marca`
--
ALTER TABLE `marca`
  ADD PRIMARY KEY (`cod_marca`);

--
-- Indices de la tabla `metodo_pago`
--
ALTER TABLE `metodo_pago`
  ADD PRIMARY KEY (`cod_metodo`);

--
-- Indices de la tabla `modelo`
--
ALTER TABLE `modelo`
  ADD PRIMARY KEY (`cod_modelo`),
  ADD KEY `fk_modelo_marca` (`cod_marca`);

--
-- Indices de la tabla `moneda`
--
ALTER TABLE `moneda`
  ADD PRIMARY KEY (`cod_moneda`);

--
-- Indices de la tabla `moneda_digital`
--
ALTER TABLE `moneda_digital`
  ADD PRIMARY KEY (`cod_mon_digital`);

--
-- Indices de la tabla `pago_cuentas`
--
ALTER TABLE `pago_cuentas`
  ADD PRIMARY KEY (`cod_pagos`),
  ADD KEY `fk_pagocuenta_cpc` (`cod_cuentas`),
  ADD KEY `idx_pago_referencia` (`referencia`);

--
-- Indices de la tabla `pago_cuota_detalle`
--
ALTER TABLE `pago_cuota_detalle`
  ADD PRIMARY KEY (`cod_pago_cuota`),
  ADD KEY `fk_pcd_pago` (`cod_pagos`),
  ADD KEY `fk_pcd_cuota` (`cod_cuota`);

--
-- Indices de la tabla `propietario`
--
ALTER TABLE `propietario`
  ADD PRIMARY KEY (`cedula_propietario`);

--
-- Indices de la tabla `proveedor_compra`
--
ALTER TABLE `proveedor_compra`
  ADD PRIMARY KEY (`rif_cedula_proveedor`);

--
-- Indices de la tabla `servicios`
--
ALTER TABLE `servicios`
  ADD PRIMARY KEY (`cod_servicios`);

--
-- Indices de la tabla `taller`
--
ALTER TABLE `taller`
  ADD PRIMARY KEY (`cod_taller`);

--
-- Indices de la tabla `tasa_cambio`
--
ALTER TABLE `tasa_cambio`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `tipo_vehiculo`
--
ALTER TABLE `tipo_vehiculo`
  ADD PRIMARY KEY (`cod_tipo`);

--
-- Indices de la tabla `vehiculo`
--
ALTER TABLE `vehiculo`
  ADD PRIMARY KEY (`placa`),
  ADD UNIQUE KEY `uk_cod_documento` (`cod_documento`),
  ADD UNIQUE KEY `uk_cod_accesorio` (`cod_accesorio`),
  ADD KEY `fk_vehiculo_modelo` (`cod_modelo`),
  ADD KEY `cod_tipo` (`cod_tipo`),
  ADD KEY `cedula_propietario` (`cedula_propietario`);

--
-- Indices de la tabla `ventas`
--
ALTER TABLE `ventas`
  ADD PRIMARY KEY (`cod_venta`),
  ADD KEY `cedula_usuario` (`cedula_usuario`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `accesorio`
--
ALTER TABLE `accesorio`
  MODIFY `cod_accesorio` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- AUTO_INCREMENT de la tabla `banco`
--
ALTER TABLE `banco`
  MODIFY `cod_banco` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `catalogo`
--
ALTER TABLE `catalogo`
  MODIFY `cod_catalogo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- AUTO_INCREMENT de la tabla `citas`
--
ALTER TABLE `citas`
  MODIFY `cod_citas` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `compras_accesorios`
--
ALTER TABLE `compras_accesorios`
  MODIFY `cod_compras` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `cuentas_por_cobrar`
--
ALTER TABLE `cuentas_por_cobrar`
  MODIFY `cod_cuentas` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `cuotas`
--
ALTER TABLE `cuotas`
  MODIFY `cod_cuota` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT de la tabla `det_banco`
--
ALTER TABLE `det_banco`
  MODIFY `cod_det_banco` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `det_compra`
--
ALTER TABLE `det_compra`
  MODIFY `cod_det_compra` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `det_mantenimiento`
--
ALTER TABLE `det_mantenimiento`
  MODIFY `cod_detalle` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `det_nom_digital`
--
ALTER TABLE `det_nom_digital`
  MODIFY `cod_det_digital` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `det_pago`
--
ALTER TABLE `det_pago`
  MODIFY `cod_det_pago` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

--
-- AUTO_INCREMENT de la tabla `det_salida`
--
ALTER TABLE `det_salida`
  MODIFY `cod_salida` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `det_servicios`
--
ALTER TABLE `det_servicios`
  MODIFY `cod_det_servicio` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `det_venta`
--
ALTER TABLE `det_venta`
  MODIFY `cod_det_venta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `documentacion`
--
ALTER TABLE `documentacion`
  MODIFY `cod_documento` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- AUTO_INCREMENT de la tabla `historia_estado_vehiculo`
--
ALTER TABLE `historia_estado_vehiculo`
  MODIFY `cod_historia` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=46;

--
-- AUTO_INCREMENT de la tabla `imagen`
--
ALTER TABLE `imagen`
  MODIFY `cod_imagen` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- AUTO_INCREMENT de la tabla `insumos`
--
ALTER TABLE `insumos`
  MODIFY `cod_insumo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `mantenimiento`
--
ALTER TABLE `mantenimiento`
  MODIFY `cod_mantenimiento` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `mantenimiento_cant`
--
ALTER TABLE `mantenimiento_cant`
  MODIFY `cod_detalle_mant` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `marca`
--
ALTER TABLE `marca`
  MODIFY `cod_marca` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `metodo_pago`
--
ALTER TABLE `metodo_pago`
  MODIFY `cod_metodo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `modelo`
--
ALTER TABLE `modelo`
  MODIFY `cod_modelo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `moneda`
--
ALTER TABLE `moneda`
  MODIFY `cod_moneda` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `moneda_digital`
--
ALTER TABLE `moneda_digital`
  MODIFY `cod_mon_digital` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `pago_cuentas`
--
ALTER TABLE `pago_cuentas`
  MODIFY `cod_pagos` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

--
-- AUTO_INCREMENT de la tabla `pago_cuota_detalle`
--
ALTER TABLE `pago_cuota_detalle`
  MODIFY `cod_pago_cuota` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `servicios`
--
ALTER TABLE `servicios`
  MODIFY `cod_servicios` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `taller`
--
ALTER TABLE `taller`
  MODIFY `cod_taller` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `tasa_cambio`
--
ALTER TABLE `tasa_cambio`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT de la tabla `tipo_vehiculo`
--
ALTER TABLE `tipo_vehiculo`
  MODIFY `cod_tipo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `ventas`
--
ALTER TABLE `ventas`
  MODIFY `cod_venta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `catalogo`
--
ALTER TABLE `catalogo`
  ADD CONSTRAINT `fk_cat_vehiculo` FOREIGN KEY (`placa`) REFERENCES `vehiculo` (`placa`);

--
-- Filtros para la tabla `citas`
--
ALTER TABLE `citas`
  ADD CONSTRAINT `fk_citas_cat` FOREIGN KEY (`cod_catalogo`) REFERENCES `catalogo` (`cod_catalogo`);

--
-- Filtros para la tabla `compras_accesorios`
--
ALTER TABLE `compras_accesorios`
  ADD CONSTRAINT `compras_accesorios_ibfk_1` FOREIGN KEY (`rif_cedula_proveedor`) REFERENCES `proveedor_compra` (`rif_cedula_proveedor`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `cuentas_por_cobrar`
--
ALTER TABLE `cuentas_por_cobrar`
  ADD CONSTRAINT `fk_cpc_venta` FOREIGN KEY (`cod_venta`) REFERENCES `ventas` (`cod_venta`) ON DELETE CASCADE;

--
-- Filtros para la tabla `cuotas`
--
ALTER TABLE `cuotas`
  ADD CONSTRAINT `fk_cuotas_cxc` FOREIGN KEY (`cod_cuentas`) REFERENCES `cuentas_por_cobrar` (`cod_cuentas`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `det_banco`
--
ALTER TABLE `det_banco`
  ADD CONSTRAINT `fk_detbanco_banco` FOREIGN KEY (`cod_banco`) REFERENCES `banco` (`cod_banco`),
  ADD CONSTRAINT `fk_detbanco_pago` FOREIGN KEY (`cod_det_pago`) REFERENCES `det_pago` (`cod_det_pago`);

--
-- Filtros para la tabla `det_compra`
--
ALTER TABLE `det_compra`
  ADD CONSTRAINT `fk_detcomp_compra` FOREIGN KEY (`cod_compras`) REFERENCES `compras_accesorios` (`cod_compras`),
  ADD CONSTRAINT `fk_detcomp_insumo` FOREIGN KEY (`cod_insumo`) REFERENCES `insumos` (`cod_insumo`);

--
-- Filtros para la tabla `det_mantenimiento`
--
ALTER TABLE `det_mantenimiento`
  ADD CONSTRAINT `fk_detmant_mant` FOREIGN KEY (`cod_mantenimiento`) REFERENCES `mantenimiento` (`cod_mantenimiento`),
  ADD CONSTRAINT `fk_detmant_taller` FOREIGN KEY (`cod_taller`) REFERENCES `taller` (`cod_taller`),
  ADD CONSTRAINT `fk_detmant_veh` FOREIGN KEY (`placa`) REFERENCES `vehiculo` (`placa`);

--
-- Filtros para la tabla `det_nom_digital`
--
ALTER TABLE `det_nom_digital`
  ADD CONSTRAINT `fk_detdig_moneda` FOREIGN KEY (`cod_mon_digital`) REFERENCES `moneda_digital` (`cod_mon_digital`),
  ADD CONSTRAINT `fk_detdig_pago` FOREIGN KEY (`cod_det_pago`) REFERENCES `det_pago` (`cod_det_pago`);

--
-- Filtros para la tabla `det_pago`
--
ALTER TABLE `det_pago`
  ADD CONSTRAINT `fk_detpago_metodo` FOREIGN KEY (`cod_metodo`) REFERENCES `metodo_pago` (`cod_metodo`),
  ADD CONSTRAINT `fk_detpago_moneda` FOREIGN KEY (`cod_moneda`) REFERENCES `moneda` (`cod_moneda`),
  ADD CONSTRAINT `fk_detpago_pagocuenta` FOREIGN KEY (`cod_pagos`) REFERENCES `pago_cuentas` (`cod_pagos`);

--
-- Filtros para la tabla `det_salida`
--
ALTER TABLE `det_salida`
  ADD CONSTRAINT `det_salida_ibfk_1` FOREIGN KEY (`placa`) REFERENCES `vehiculo` (`placa`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `det_salida_ibfk_2` FOREIGN KEY (`cod_insumo`) REFERENCES `insumos` (`cod_insumo`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `det_servicios`
--
ALTER TABLE `det_servicios`
  ADD CONSTRAINT `fk_detserv_serv` FOREIGN KEY (`cod_servicios`) REFERENCES `servicios` (`cod_servicios`),
  ADD CONSTRAINT `fk_detserv_veh` FOREIGN KEY (`placa`) REFERENCES `vehiculo` (`placa`);

--
-- Filtros para la tabla `det_venta`
--
ALTER TABLE `det_venta`
  ADD CONSTRAINT `fk_detventa_veh` FOREIGN KEY (`placa`) REFERENCES `vehiculo` (`placa`),
  ADD CONSTRAINT `fk_detventa_venta` FOREIGN KEY (`cod_venta`) REFERENCES `ventas` (`cod_venta`) ON DELETE CASCADE;

--
-- Filtros para la tabla `historia_estado_vehiculo`
--
ALTER TABLE `historia_estado_vehiculo`
  ADD CONSTRAINT `fk_hist_vehiculo` FOREIGN KEY (`placa`) REFERENCES `vehiculo` (`placa`) ON DELETE CASCADE;

--
-- Filtros para la tabla `imagen`
--
ALTER TABLE `imagen`
  ADD CONSTRAINT `fk_img_vehiculo` FOREIGN KEY (`placa`) REFERENCES `vehiculo` (`placa`);

--
-- Filtros para la tabla `mantenimiento_cant`
--
ALTER TABLE `mantenimiento_cant`
  ADD CONSTRAINT `mantenimiento_cant_ibfk_1` FOREIGN KEY (`cod_mantenimiento`) REFERENCES `mantenimiento` (`cod_mantenimiento`) ON DELETE CASCADE;

--
-- Filtros para la tabla `modelo`
--
ALTER TABLE `modelo`
  ADD CONSTRAINT `fk_modelo_marca` FOREIGN KEY (`cod_marca`) REFERENCES `marca` (`cod_marca`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `pago_cuentas`
--
ALTER TABLE `pago_cuentas`
  ADD CONSTRAINT `fk_pagocuenta_cpc` FOREIGN KEY (`cod_cuentas`) REFERENCES `cuentas_por_cobrar` (`cod_cuentas`);

--
-- Filtros para la tabla `pago_cuota_detalle`
--
ALTER TABLE `pago_cuota_detalle`
  ADD CONSTRAINT `fk_pcd_cuota` FOREIGN KEY (`cod_cuota`) REFERENCES `cuotas` (`cod_cuota`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_pcd_pago` FOREIGN KEY (`cod_pagos`) REFERENCES `pago_cuentas` (`cod_pagos`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `vehiculo`
--
ALTER TABLE `vehiculo`
  ADD CONSTRAINT `fk_vehiculo_acc` FOREIGN KEY (`cod_accesorio`) REFERENCES `accesorio` (`cod_accesorio`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_vehiculo_doc` FOREIGN KEY (`cod_documento`) REFERENCES `documentacion` (`cod_documento`),
  ADD CONSTRAINT `fk_vehiculo_modelo` FOREIGN KEY (`cod_modelo`) REFERENCES `modelo` (`cod_modelo`),
  ADD CONSTRAINT `fk_vehiculo_prov` FOREIGN KEY (`cedula_propietario`) REFERENCES `propietario` (`cedula_propietario`),
  ADD CONSTRAINT `vehiculo_ibfk_1` FOREIGN KEY (`cod_tipo`) REFERENCES `tipo_vehiculo` (`cod_tipo`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
