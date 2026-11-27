import unittest
from unittest.mock import MagicMock, patch

from models.compra import CompraModel, ESTADO_PENDIENTE, ESTADO_ANULADA


class TestCompraModel(unittest.TestCase):

    def setUp(self):
        self.conexion = MagicMock()
        self.cursor = MagicMock()
        self.conexion.cursor.return_value = self.cursor

        self.patch_conexion = patch(
            "models.compra.ConexionBD.obtener_conexion",
            return_value=self.conexion
        )
        self.patch_conexion.start()
        self.addCleanup(self.patch_conexion.stop)

    def test_obtener_todas_excluye_anuladas_por_defecto(self):
        datos = [{"cod_compras": 1, "estado": ESTADO_PENDIENTE}]
        self.cursor.fetchall.return_value = datos

        resultado = CompraModel.obtener_todas()

        self.conexion.cursor.assert_called_once_with(dictionary=True)
        consulta, parametros = self.cursor.execute.call_args[0]
        self.assertIn("compras_accesorios", consulta)
        self.assertIn("WHERE c.estado <> %s", consulta)
        self.assertEqual(parametros, (ESTADO_ANULADA,))
        self.assertEqual(resultado, datos)
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_obtener_todas_incluye_anuladas_si_se_solicita(self):
        self.cursor.fetchall.return_value = []

        resultado = CompraModel.obtener_todas(incluir_anuladas=True)

        consulta = self.cursor.execute.call_args[0][0]
        self.assertIn("compras_accesorios", consulta)
        self.assertNotIn("WHERE c.estado <> %s", consulta)
        self.cursor.execute.assert_called_once_with(consulta)
        self.assertEqual(resultado, [])

    def test_obtener_por_id_devuelve_none_si_no_existe(self):
        self.cursor.fetchone.return_value = None

        resultado = CompraModel.obtener_por_id(100)

        self.assertIsNone(resultado)
        self.assertEqual(self.cursor.execute.call_count, 1)
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_obtener_por_id_devuelve_cabecera_y_detalles(self):
        cabecera = {"cod_compras": 7, "estado": ESTADO_PENDIENTE}
        detalles = [{"cod_det_compra": 2, "cod_insumo": 3, "cantidad": 4}]
        self.cursor.fetchone.return_value = cabecera
        self.cursor.fetchall.return_value = detalles

        resultado = CompraModel.obtener_por_id(7)

        self.assertEqual(resultado["cod_compras"], 7)
        self.assertEqual(resultado["detalles"], detalles)
        self.assertEqual(self.cursor.execute.call_count, 2)

    @patch("models.compra.ValidacionCompra.validar_cabecera",
           return_value=(False, {"rif_cedula_proveedor": "Proveedor inválido"}))
    def test_crear_rechaza_cabecera_invalida(self, _validacion):
        with self.assertRaisesRegex(Exception, "Validación: Proveedor inválido"):
            CompraModel.crear("J-123", "Normal", "")

        self.obtener_conexion.assert_not_called()

    @patch("models.compra.ValidacionCompra.validar_cabecera",
           return_value=(True, {}))
    def test_crear_rechaza_proveedor_inexistente_o_inactivo(self, _validacion):
        self.cursor.fetchone.return_value = None

        with self.assertRaisesRegex(Exception, "proveedor no existe o está inactivo"):
            CompraModel.crear("J-123", "Normal", "")

        self.conexion.rollback.assert_not_called()
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    @patch("models.compra.ValidacionCompra.validar_cabecera",
           return_value=(True, {}))
    @patch("models.compra.date")
    def test_crear_registra_compra_pendiente(self, fecha_mock, _validacion):
        fecha_mock.today.return_value = "2026-01-15"
        self.cursor.fetchone.return_value = (1,)
        self.cursor.lastrowid = 25

        resultado = CompraModel.crear(
            "J-123", " Normal ", " Compra inicial ", id_usuario_sesion=None
        )

        self.assertEqual(resultado, 25)
        self.assertEqual(self.cursor.execute.call_count, 2)
        consulta_insert, parametros = self.cursor.execute.call_args_list[1][0]
        self.assertIn("INSERT INTO compras_accesorios", consulta_insert)
        self.assertEqual(parametros[2], "Normal")
        self.assertEqual(parametros[3], ESTADO_PENDIENTE)
        self.assertEqual(parametros[4], "Compra inicial")
        self.conexion.commit.assert_called_once()
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_actualizar_estado_rechaza_estado_invalido(self):
        with self.assertRaisesRegex(Exception, "estado inválido"):
            CompraModel.actualizar_estado(1, "Desconocido")

        self.obtener_conexion.assert_not_called()

    def test_actualizar_estado_devuelve_true_si_actualiza(self):
        self.cursor.rowcount = 1

        resultado = CompraModel.actualizar_estado(1, ESTADO_PENDIENTE)

        self.assertTrue(resultado)
        consulta, parametros = self.cursor.execute.call_args[0]
        self.assertIn("UPDATE compras_accesorios", consulta)
        self.assertEqual(parametros, (ESTADO_PENDIENTE, 1))
        self.conexion.commit.assert_called_once()

    def test_actualizar_estado_devuelve_false_si_no_hay_filas(self):
        self.cursor.rowcount = 0

        resultado = CompraModel.actualizar_estado(999, ESTADO_PENDIENTE)

        self.assertFalse(resultado)
        self.conexion.commit.assert_called_once()

    def test_eliminar_devuelve_error_si_compra_no_existe(self):
        self.cursor.fetchone.return_value = None

        resultado = CompraModel.eliminar(999)

        self.assertFalse(resultado["status"])
        self.assertEqual(resultado["mensaje"], "La compra no existe.")
        self.conexion.commit.assert_not_called()

    def test_eliminar_devuelve_error_si_ya_esta_anulada(self):
        self.cursor.fetchone.return_value = {"estado": ESTADO_ANULADA}

        resultado = CompraModel.eliminar(1)

        self.assertFalse(resultado["status"])
        self.assertEqual(resultado["mensaje"], "La compra ya estaba anulada.")
        self.conexion.commit.assert_not_called()

    def test_eliminar_anula_compra_y_confirma_transaccion(self):
        self.cursor.fetchone.return_value = {"estado": ESTADO_PENDIENTE}
        self.cursor.rowcount = 1

        resultado = CompraModel.eliminar(1)

        self.assertTrue(resultado["status"])
        self.assertIn("anulada", resultado["mensaje"])
        self.assertEqual(self.cursor.execute.call_count, 3)
        self.conexion.commit.assert_called_once()
        self.conexion.rollback.assert_not_called()

    def test_reactivar_rechaza_compra_inexistente(self):
        self.cursor.fetchone.return_value = None

        resultado = CompraModel.reactivar(999)

        self.assertFalse(resultado["status"])
        self.assertEqual(resultado["mensaje"], "La compra no existe.")
        self.conexion.commit.assert_not_called()

    def test_reactivar_rechaza_compra_no_anulada(self):
        self.cursor.fetchone.return_value = {"estado": ESTADO_PENDIENTE}

        resultado = CompraModel.reactivar(1)

        self.assertFalse(resultado["status"])
        self.assertIn("Solo se pueden reactivar", resultado["mensaje"])
        self.conexion.commit.assert_not_called()

    def test_reactivar_compra_anulada_y_restaura_stock(self):
        self.cursor.fetchone.return_value = {"estado": ESTADO_ANULADA}
        self.cursor.rowcount = 1

        resultado = CompraModel.reactivar(1)

        self.assertTrue(resultado["status"])
        self.assertIn("stock restaurado", resultado["mensaje"])
        self.assertEqual(self.cursor.execute.call_count, 3)
        self.conexion.commit.assert_called_once()
        self.conexion.rollback.assert_not_called()

    @patch("models.compra.ValidacionCompra.validar_detalle",
           return_value=(False, {"cantidad": "Cantidad inválida"}))
    def test_agregar_detalle_rechaza_datos_invalidos(self, _validacion):
        resultado = CompraModel.agregar_detalle(1, 2, 0)

        self.assertFalse(resultado["status"])
        self.assertEqual(resultado["mensaje"], "Cantidad inválida")
        self.obtener_conexion.assert_not_called()

    @patch("models.compra.ValidacionCompra.validar_detalle",
           return_value=(True, {}))
    def test_agregar_detalle_rechaza_compra_inexistente(self, _validacion):
        self.cursor.fetchone.return_value = None

        resultado = CompraModel.agregar_detalle(999, 2, 3)

        self.assertFalse(resultado["status"])
        self.assertEqual(resultado["mensaje"], "La compra no existe.")
        self.conexion.commit.assert_not_called()

    @patch("models.compra.ValidacionCompra.validar_detalle",
           return_value=(True, {}))
    def test_agregar_detalle_rechaza_compra_anulada(self, _validacion):
        self.cursor.fetchone.return_value = (ESTADO_ANULADA,)

        resultado = CompraModel.agregar_detalle(1, 2, 3)

        self.assertFalse(resultado["status"])
        self.assertIn("compra anulada", resultado["mensaje"])
        self.conexion.commit.assert_not_called()

    @patch("models.compra.ValidacionCompra.validar_detalle",
           return_value=(True, {}))
    def test_agregar_detalle_rechaza_insumo_inactivo_o_inexistente(self, _validacion):
        self.cursor.fetchone.side_effect = [(ESTADO_PENDIENTE,), None]

        resultado = CompraModel.agregar_detalle(1, 2, 3)

        self.assertFalse(resultado["status"])
        self.assertIn("insumo no existe o está inactivo", resultado["mensaje"])
        self.conexion.commit.assert_not_called()

    @patch("models.compra.ValidacionCompra.validar_detalle",
           return_value=(True, {}))
    def test_agregar_detalle_inserta_y_suma_stock(self, _validacion):
        self.cursor.fetchone.side_effect = [(ESTADO_PENDIENTE,), (1,)]

        resultado = CompraModel.agregar_detalle(1, 2, 5)

        self.assertTrue(resultado["status"])
        self.assertEqual(self.cursor.execute.call_count, 4)
        self.conexion.commit.assert_called_once()
        self.conexion.rollback.assert_not_called()

    def test_eliminar_detalle_rechaza_detalle_inexistente(self):
        self.cursor.fetchone.return_value = None

        resultado = CompraModel.eliminar_detalle(99)

        self.assertFalse(resultado["status"])
        self.assertEqual(resultado["mensaje"], "El detalle no existe.")
        self.conexion.commit.assert_not_called()

    def test_eliminar_detalle_rechaza_compra_anulada(self):
        self.cursor.fetchone.return_value = {
            "cod_insumo": 2,
            "cantidad": 4,
            "estado_compra": ESTADO_ANULADA,
        }

        resultado = CompraModel.eliminar_detalle(5)

        self.assertFalse(resultado["status"])
        self.assertIn("compra está anulada", resultado["mensaje"])
        self.conexion.commit.assert_not_called()

    def test_eliminar_detalle_rechaza_stock_insuficiente(self):
        self.cursor.fetchone.side_effect = [
            {"cod_insumo": 2, "cantidad": 4, "estado_compra": ESTADO_PENDIENTE},
            {"stock": 2},
        ]

        resultado = CompraModel.eliminar_detalle(5)

        self.assertFalse(resultado["status"])
        self.assertIn("Stock insuficiente", resultado["mensaje"])
        self.conexion.commit.assert_not_called()

    def test_eliminar_detalle_elimina_y_resta_stock(self):
        self.cursor.fetchone.side_effect = [
            {"cod_insumo": 2, "cantidad": 4, "estado_compra": ESTADO_PENDIENTE},
            {"stock": 10},
        ]

        resultado = CompraModel.eliminar_detalle(5)

        self.assertTrue(resultado["status"])
        self.assertEqual(self.cursor.execute.call_count, 4)
        self.conexion.commit.assert_called_once()

    def test_obtener_proveedores_solo_activos_por_defecto(self):
        proveedores = [{"rif_cedula_proveedor": "J-123", "estado": "Activo"}]
        self.cursor.fetchall.return_value = proveedores

        resultado = CompraModel.obtener_proveedores()

        consulta = self.cursor.execute.call_args[0][0]
        self.assertIn("WHERE estado = 'Activo'", consulta)
        self.assertEqual(resultado, proveedores)

    def test_obtener_proveedores_puede_incluir_inactivos(self):
        self.cursor.fetchall.return_value = []

        CompraModel.obtener_proveedores(solo_activos=False)

        consulta = self.cursor.execute.call_args[0][0]
        self.assertNotIn("WHERE estado = 'Activo'", consulta)

    def test_obtener_proveedor_por_rif(self):
        proveedor = {"rif_cedula_proveedor": "J-123", "razon_social": "Proveedor"}
        self.cursor.fetchone.return_value = proveedor

        resultado = CompraModel.obtener_proveedor_por_rif("J-123")

        self.assertEqual(resultado, proveedor)
        self.cursor.execute.assert_called_once()
        self.assertEqual(self.cursor.execute.call_args[0][1], ("J-123",))

    @patch("models.compra.ValidacionCompra.validar_proveedor",
           return_value=(False, {"rif": "RIF inválido"}))
    def test_crear_proveedor_rechaza_datos_invalidos(self, _validacion):
        with self.assertRaisesRegex(Exception, "Validación: RIF inválido"):
            CompraModel.crear_proveedor(
                "J-123", "Proveedor", "Dirección", "04120000000", "a@b.com"
            )
        self.obtener_conexion.assert_not_called()

    @patch("models.compra.ValidacionCompra.validar_proveedor",
           return_value=(True, {}))
    def test_crear_proveedor_inserta_y_confirma(self, _validacion):
        resultado = CompraModel.crear_proveedor(
            "J-123", " Proveedor ", " Dirección ", "04120000000",
            " correo@ejemplo.com "
        )

        self.assertTrue(resultado)
        consulta, parametros = self.cursor.execute.call_args[0]
        self.assertIn("INSERT INTO proveedor_compra", consulta)
        self.assertEqual(parametros[0], "J-123")
        self.assertEqual(parametros[1], "Proveedor")
        self.assertEqual(parametros[2], "Dirección")
        self.conexion.commit.assert_called_once()

    @patch("models.compra.ValidacionCompra.validar_proveedor",
           return_value=(False, {"correo": "Correo inválido"}))
    def test_actualizar_proveedor_rechaza_datos_invalidos(self, _validacion):
        with self.assertRaisesRegex(Exception, "Validación: Correo inválido"):
            CompraModel.actualizar_proveedor(
                "J-123", "Proveedor", "Dirección", "04120000000", "correo"
            )
        self.obtener_conexion.assert_not_called()

    @patch("models.compra.ValidacionCompra.validar_proveedor",
           return_value=(True, {}))
    def test_actualizar_proveedor_devuelve_true_si_modifica(self, _validacion):
        self.cursor.rowcount = 1

        resultado = CompraModel.actualizar_proveedor(
            "J-123", " Proveedor ", " Dirección ", "04120000000",
            " correo@ejemplo.com ", "Activo"
        )

        self.assertTrue(resultado)
        consulta, parametros = self.cursor.execute.call_args[0]
        self.assertIn("UPDATE proveedor_compra", consulta)
        self.assertEqual(parametros[0], "Proveedor")
        self.assertEqual(parametros[-1], "J-123")
        self.conexion.commit.assert_called_once()

    @patch("models.compra.ValidacionCompra.validar_proveedor",
           return_value=(True, {}))
    def test_actualizar_proveedor_devuelve_false_si_no_hay_filas(self, _validacion):
        self.cursor.rowcount = 0

        resultado = CompraModel.actualizar_proveedor(
            "J-999", "Proveedor", "Dirección", "04120000000",
            "correo@ejemplo.com", "Activo"
        )

        self.assertFalse(resultado)
        self.conexion.commit.assert_called_once()

    def test_eliminar_proveedor_inactiva_registro(self):
        self.cursor.rowcount = 1

        resultado = CompraModel.eliminar_proveedor("J-123")

        consulta, parametros = self.cursor.execute.call_args[0]
        self.assertIn("UPDATE proveedor_compra", consulta)
        self.assertIn("Inactivo", consulta)
        self.assertEqual(parametros, ("J-123",))
        self.assertTrue(resultado)
        self.conexion.commit.assert_called_once()

    def test_obtener_insumos_activos(self):
        insumos = [{"cod_insumo": 1, "nombre_insumo": "Aceite", "stock": 5}]
        self.cursor.fetchall.return_value = insumos

        resultado = CompraModel.obtener_insumos_activos()

        consulta = self.cursor.execute.call_args[0][0]
        self.assertIn("FROM insumos", consulta)
        self.assertIn("WHERE estado = 1", consulta)
        self.assertEqual(resultado, insumos)

    def test_obtener_insumo_por_id(self):
        insumo = {"cod_insumo": 2, "nombre_insumo": "Filtro", "stock": 3}
        self.cursor.fetchone.return_value = insumo

        resultado = CompraModel.obtener_insumo_por_id(2)

        self.assertEqual(resultado, insumo)
        self.assertEqual(self.cursor.execute.call_args[0][1], (2,))


if __name__ == "__main__":
    unittest.main()
