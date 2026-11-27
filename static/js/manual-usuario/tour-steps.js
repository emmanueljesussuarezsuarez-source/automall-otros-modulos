/**
 * AutoMall - Centro de Ayuda y Manual Interactivo
 * Módulo: tour-steps.js
 * Registro declarativo de pasos de las visitas guiadas estructurado en Actions y Props.
 * Soporta subtours específicos por módulo (visión general, registros, formularios, reportes).
 * Respeta permisos reales: los pasos condicionales solo se muestran si el elemento
 * correspondiente está presente en el DOM (protegido por Jinja2 del backend).
 */

export class TourSteps {
    /**
     * Catálogo completo de módulos y sus recorridos por tareas
     */
    static getModuleDefinitions() {
        return {
            // ==================================================================
            // 1. INICIO / PORTAL PRINCIPAL
            // ==================================================================
            inicio: {
                nombre: 'Inicio / Portal Principal',
                icono: 'bi-house-door-fill',
                ruta: '/',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Conocer el portal de inicio',
                        icono: 'bi-info-circle',
                        descripcion: 'Bienvenida, carrusel de novedades, buscador y accesos rápidos.',
                        pasos: [
                            {
                                target: '#heroCarousel',
                                title: 'Bienvenido a AutoMall',
                                content: 'El portal principal presenta las novedades automotrices, banners institucionales y accesos a la información del concesionario.',
                                placement: 'bottom'
                            },
                            {
                                target: '.search-container .search-bar, .search-bar',
                                title: 'Búsqueda Rápida del Catálogo',
                                content: 'Encuentra vehículos al instante filtrando por marca, modelo o año directamente desde la pantalla inicial.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('.search-bar')
                            },
                            {
                                target: '.alert.border-primary',
                                title: 'Panel de Control del Usuario',
                                content: 'Indica tu sesión activa y te recuerda que puedes gestionar el inventario mediante el menú superior según tu rol.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('.alert.border-primary')
                            },
                            {
                                target: '.section-title, .card-vehiculo',
                                title: 'Vitrina de Vehículos Destacados',
                                content: 'Muestra las unidades disponibles más recientes con fotografía, año y precio en divisa ($).',
                                placement: 'top',
                                condition: () => !!document.querySelector('.card-vehiculo')
                            },
                            {
                                target: '[data-bs-target="#modalDetalleVenta"]',
                                title: 'Ficha Técnica en Modal',
                                content: 'Al presionar "Ver Detalles" puedes inspeccionar la descripción, equipamiento y galería fotográfica sin abandonar la página de inicio.',
                                placement: 'top',
                                condition: () => !!document.querySelector('[data-bs-target="#modalDetalleVenta"]')
                            },
                            {
                                target: '#navNotificaciones',
                                title: 'Campana de Avisos Administrativos',
                                content: 'Aquí recibes alertas de órdenes completadas, citas pendientes y notificaciones del sistema en tiempo real.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('navNotificaciones')
                            },
                            {
                                target: '#btnAbrirCentroAyuda',
                                title: 'Centro de Ayuda y Manual Interactivo',
                                content: 'En cualquier momento puedes pulsar este botón para consultar guías interactivas de todos los módulos autorizados.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('btnAbrirCentroAyuda')
                            },
                            {
                                target: null,
                                title: '¡Exploración de Inicio Completada!',
                                content: 'Has conocido las herramientas principales del portal. Explora otros módulos desde el Centro de Ayuda.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 2. TALLER DE VEHÍCULOS
            // ==================================================================
            taller: {
                nombre: 'Taller de Vehículos',
                icono: 'bi-building',
                ruta: '/taller',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Conocer el módulo',
                        icono: 'bi-info-circle',
                        descripcion: 'Visión general del inventario, columnas, estados operativos y notificaciones.',
                        pasos: [
                            {
                                target: '[data-tour="taller-header"], .card-header',
                                title: 'Propósito del Módulo de Talleres',
                                content: 'Este panel centraliza la red de talleres aliados que realizan reparaciones mecánicas y servicios de acondicionamiento para la flota de AutoMall.',
                                placement: 'bottom'
                            },
                            {
                                target: '[data-tour="taller-tabla"], #tablaTalleres',
                                title: 'Inventario de Talleres Registrados',
                                content: 'En esta tabla interactiva puedes consultar todos los talleres disponibles, buscar por palabras clave y ordenar los datos por columnas.',
                                placement: 'top'
                            },
                            {
                                target: '[data-tour="taller-columnas"], #tablaTalleres thead',
                                title: 'Columnas Principales',
                                content: 'Cada fila muestra el código (#ID), denominación comercial, dirección de la sede y el estado operativo del taller.',
                                placement: 'bottom'
                            },
                            {
                                target: '[data-tour="taller-estado"], #tablaTalleres tbody tr td .badge',
                                title: 'Control de Estado Operativo',
                                content: 'La etiqueta verde indica un taller Activo apto para recibir órdenes. Los talleres Inactivos no pueden ser asignados a nuevos mantenimientos.',
                                placement: 'top',
                                condition: () => !!document.querySelector('[data-tour="taller-estado"], #tablaTalleres tbody tr td .badge')
                            },
                            {
                                target: '[data-tour="taller-btn-eliminar"], .btn-eliminar-taller',
                                title: 'Inactivación Lógica',
                                content: 'La eliminación es lógica: el taller no se borra físicamente de la base de datos, sino que conmuta a inactivo para preservar el historial.',
                                placement: 'left',
                                condition: () => !!document.querySelector('[data-tour="taller-btn-eliminar"], .btn-eliminar-taller')
                            },
                            {
                                target: '#navNotificaciones',
                                title: 'Notificaciones de la Campana',
                                content: 'Al registrar o modificar talleres, el sistema crea automáticamente una notificación interna para el personal de administración en esta campana.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('navNotificaciones')
                            },
                            {
                                target: null,
                                title: 'Resumen y Próximos Recorridos',
                                content: 'Has conocido la estructura general del módulo. Para aprender a usar los formularios, puedes iniciar los recorridos "Registrar" o "Editar".',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un taller',
                        icono: 'bi-plus-circle',
                        descripcion: 'Paso a paso para llenar el formulario real de registro y reglas de validación.',
                        pasos: [
                            {
                                target: '[data-tour="taller-btn-registrar"], [data-bs-target="#modalRegistrarTaller"]',
                                title: 'Acceso al Formulario de Registro',
                                content: 'Presiona este botón para abrir la ventana de registro de talleres aliados. A continuación abriremos el formulario para revisar sus campos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('[data-tour="taller-btn-registrar"], [data-bs-target="#modalRegistrarTaller"]')
                            },
                            {
                                target: '#modalRegistrarTaller .modal-content',
                                title: 'Formulario de Alta de Taller',
                                content: 'Esta ventana permite afiliar un nuevo taller. Ningún campo modificará datos reales durante esta visita guiada.',
                                placement: 'center',
                                action: async () => {
                                    const modalEl = document.getElementById('modalRegistrarTaller');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#nombre_taller',
                                title: 'Nombre del Taller (Obligatorio)',
                                content: 'Ingresa el nombre comercial. Requisitos del sistema: entre 3 y 100 caracteres alfanuméricos y no puede repetirse con otro taller existente.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre_taller')
                            },
                            {
                                target: '#direccion',
                                title: 'Dirección Física (Obligatorio)',
                                content: 'Indica la ubicación física de la sede o taller mecánico. Requisitos: entre 5 y 255 caracteres descriptivos.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('direccion')
                            },
                            {
                                target: '#modalRegistrarTaller button[type="submit"]',
                                title: 'Botón Guardar',
                                content: 'Al hacer clic, el sistema verifica que los datos cumplan las validaciones y registra el taller en estado Activo. (No lo presiones durante la guía).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalRegistrarTaller button[type="submit"]')
                            },
                            {
                                target: '#modalRegistrarTaller button[data-bs-dismiss="modal"]',
                                title: 'Botón Cancelar',
                                content: 'Presiona Cancelar para cerrar la ventana sin guardar nada ni alterar el sistema.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalRegistrarTaller button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalRegistrarTaller');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: 'Mensajes de Validación y Éxito',
                                content: 'Al guardar con éxito o si falta algún campo, el sistema muestra alertas visuales temporales (SweetAlert2) detallando el resultado de la operación.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía de Registro'
                            }
                        ]
                    },
                    edicion: {
                        id: 'edicion',
                        nombre: 'Cómo editar un taller',
                        icono: 'bi-pencil',
                        descripcion: 'Paso a paso para modificar los datos de un taller existente de forma segura.',
                        pasos: [
                            {
                                target: '[data-tour="taller-btn-editar"], .btn-editar-taller',
                                title: 'Acceso a la Edición de Taller',
                                content: 'En la columna Acciones, este botón con ícono de lápiz carga la información del taller en el formulario de modificación.',
                                placement: 'left',
                                condition: () => !!document.querySelector('[data-tour="taller-btn-editar"], .btn-editar-taller')
                            },
                            {
                                target: '#modalEditarTaller .modal-content',
                                title: 'Formulario de Modificación',
                                content: 'Esta ventana permite actualizar los datos del establecimiento manteniendo su número de registro (#ID) e historial intactos.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalEditarTaller') && !!document.querySelector('.btn-editar-taller'),
                                action: async () => {
                                    const btnEditar = document.querySelector('[data-tour="taller-btn-editar"], .btn-editar-taller');
                                    const modalEl = document.getElementById('modalEditarTaller');
                                    if (btnEditar && modalEl && typeof bootstrap !== 'undefined') {
                                        const nombre = btnEditar.dataset.nombre || '';
                                        const direccion = btnEditar.dataset.direccion || '';
                                        const inputNombre = document.getElementById('edit_nombre_taller');
                                        const inputDir = document.getElementById('edit_direccion');
                                        if (inputNombre && !inputNombre.value) inputNombre.value = nombre;
                                        if (inputDir && !inputDir.value) inputDir.value = direccion;
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#edit_nombre_taller',
                                title: 'Editar Nombre Comercial',
                                content: 'Permite corregir la denominación. Debe tener entre 3 y 100 caracteres y no coincidir con otro taller activo.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('edit_nombre_taller') && !!document.querySelector('.btn-editar-taller')
                            },
                            {
                                target: '#edit_direccion',
                                title: 'Editar Dirección Física',
                                content: 'Actualiza la sede física del taller. Debe contar con entre 5 y 255 caracteres descriptivos.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('edit_direccion') && !!document.querySelector('.btn-editar-taller')
                            },
                            {
                                target: '#modalEditarTaller button[type="submit"]',
                                title: 'Botón Actualizar',
                                content: 'Aplica las modificaciones validadas en la base de datos. (Durante esta visita no se enviará el formulario).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalEditarTaller button[type="submit"]') && !!document.querySelector('.btn-editar-taller')
                            },
                            {
                                target: '#modalEditarTaller button[data-bs-dismiss="modal"]',
                                title: 'Botón Cancelar',
                                content: 'Presiona Cancelar para descartar cualquier cambio y regresar a la tabla sin modificar el registro.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalEditarTaller button[data-bs-dismiss="modal"]') && !!document.querySelector('.btn-editar-taller'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalEditarTaller');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: '[data-tour="taller-tabla"], #tablaTalleres',
                                title: 'Sin Registros para Editar',
                                content: 'Actualmente no existen talleres en la tabla para editar. Primero debes registrar al menos un taller mediante el botón "Registrar Taller".',
                                placement: 'top',
                                condition: () => !document.querySelector('.btn-editar-taller'),
                                finishLabel: 'Entendido'
                            },
                            {
                                target: null,
                                title: '¡Guía de Edición Finalizada!',
                                content: 'Has aprendido cómo actualizar talleres aliados de forma segura y respetando las validaciones del sistema.',
                                placement: 'center',
                                condition: () => !!document.querySelector('.btn-editar-taller'),
                                finishLabel: 'Finalizar Guía de Edición'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 3. MANTENIMIENTO OPERACIONAL
            // ==================================================================
            mantenimiento_operacional: {
                nombre: 'Mantenimiento Operacional',
                icono: 'bi-wrench-adjustable',
                ruta: '/mantenimiento-operacional',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Conocer el módulo',
                        icono: 'bi-info-circle',
                        descripcion: 'Estructura de la tabla, columnas, estados operativos y acciones.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Historial de Mantenimientos',
                                content: 'Este módulo controla las reparaciones mecánicas y servicios ejecutados sobre la flota vehicular de AutoMall.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaMantenimientoOperacional',
                                title: 'Tabla de Mantenimientos',
                                content: 'Permite buscar, ordenar y filtrar órdenes por código, placa, taller o descripción.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaMantenimientoOperacional thead',
                                title: 'Columnas de la Orden',
                                content: 'Incluye el ID, descripción general, usuario autorizador, estado, tipo (Preventivo/Correctivo), fechas, placa, taller y costos base y final.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaMantenimientoOperacional tbody tr td .badge',
                                title: 'Control de Estados',
                                content: 'Activo (en proceso), Finalizado (concluido con costo final) e Inactivo (anulado lógicamente para auditoría).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaMantenimientoOperacional tbody tr td .badge')
                            },
                            {
                                target: 'a[href*="mantenimiento-operacional/editar"]',
                                title: 'Edición de la Orden',
                                content: 'Disponible solo en estado Activo para actualizar taller, tipo de mantenimiento o fechas estimadas.',
                                placement: 'left',
                                condition: () => !!document.querySelector('a[href*="mantenimiento-operacional/editar"]')
                            },
                            {
                                target: '.btn-finalizar-mantenimiento',
                                title: 'Finalización de Orden',
                                content: 'Permite registrar los detalles del trabajo ejecutado y asentar el costo final real de la reparación.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-finalizar-mantenimiento')
                            },
                            {
                                target: null,
                                title: 'Resumen del Módulo',
                                content: 'Para aprender a registrar nuevas órdenes o consultar reportes oficiales, explora los otros recorridos.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un mantenimiento',
                        icono: 'bi-plus-circle',
                        ruta: '/mantenimiento-operacional/crear',
                        descripcion: 'Paso a paso para llenar la orden real: vehículo, taller, responsable, costos y detalles.',
                        pasos: [
                            {
                                target: '.card-body',
                                title: 'Formulario de Mantenimiento Operacional',
                                content: 'Esta pantalla formaliza la emisión de una orden técnica de reparación o servicio preventivo para un vehículo de la flota.',
                                placement: 'bottom'
                            },
                            {
                                target: '#placa',
                                title: 'Vehículo a Intervenir (Obligatorio)',
                                content: 'Selecciona la placa del vehículo registrado que requiere el servicio. El sistema lista únicamente vehículos con estatus operativo.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('placa')
                            },
                            {
                                target: '#cod_taller',
                                title: 'Taller Asignado (Obligatorio)',
                                content: 'Elige el establecimiento aliado donde se llevará a cabo la reparación mecánica. Debe ser un taller activo.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('cod_taller')
                            },
                            {
                                target: '#quien_autoriza',
                                title: 'Responsable que Autoriza (Obligatorio)',
                                content: 'Asigna el usuario administrativo o supervisor que valida y aprueba la ejecución de esta orden.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('quien_autoriza')
                            },
                            {
                                target: '#tipo',
                                title: 'Tipo de Mantenimiento (Obligatorio)',
                                content: 'Indica si es "Preventivo" (inspección programada, cambio de fluidos) o "Correctivo" (reparación de fallas o averías mecánicas).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('tipo')
                            },
                            {
                                target: '#fecha_solicitud',
                                title: 'Fecha de Solicitud (Obligatorio)',
                                content: 'Fecha en que se emite la orden de trabajo. Las validaciones del sistema prohíben registrar fechas futuras.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('fecha_solicitud')
                            },
                            {
                                target: '#fecha_completada',
                                title: 'Fecha de Culminación (Opcional)',
                                content: 'Puede completarse al momento de entrega o dejarse vacía mientras el vehículo esté en reparación.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('fecha_completada')
                            },
                            {
                                target: '#descripcion_general',
                                title: 'Descripción General del Problema',
                                content: 'Campo de texto descriptivo para asentar las observaciones, ruidos o fallas reportadas por el conductor o perito.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('descripcion_general')
                            },
                            {
                                target: '#costo_base',
                                title: 'Presupuesto Base Proyectado ($)',
                                content: 'Costo inicial estimado en dólares americanos acordado con el taller para las labores descritas.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('costo_base')
                            },
                            {
                                target: '#contenedor-detalles',
                                title: 'Renglones de Detalles Específicos',
                                content: 'Permite desglosar las refacciones o tareas técnicas individuales con su respectiva cantidad.',
                                placement: 'top',
                                condition: () => !!document.getElementById('contenedor-detalles')
                            },
                            {
                                target: '#btn-agregar-detalle',
                                title: 'Agregar Más Renglones',
                                content: 'Presiona este botón verde si necesitas desglosar más ítems o repuestos dentro de la misma orden.',
                                placement: 'top',
                                condition: () => !!document.getElementById('btn-agregar-detalle')
                            },
                            {
                                target: 'button[type="submit"]',
                                title: 'Guardar la Orden',
                                content: 'Verifica los campos obligatorios, guarda la orden en estado Activo y notifica al personal responsable. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"]')
                            },
                            {
                                target: 'a.btn-secondary',
                                title: 'Cancelar y Regresar',
                                content: 'Descarta los campos digitados y te regresa al listado general de mantenimientos sin alterar datos.',
                                placement: 'top',
                                condition: () => !!document.querySelector('a.btn-secondary')
                            },
                            {
                                target: null,
                                title: '¡Guía de Registro Finalizada!',
                                content: 'Has aprendido la estructura completa y las validaciones del formulario de órdenes de mantenimiento.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía de Registro'
                            }
                        ]
                    },
                    acciones_reporte: {
                        id: 'acciones_reporte',
                        nombre: 'Reportes y recibos digitales',
                        icono: 'bi-file-earmark-text',
                        descripcion: 'Generación de informes oficiales en PDF y comprobantes de culminación.',
                        pasos: [
                            {
                                target: 'button[data-bs-target="#modalReporteMantenimiento"]',
                                title: 'Generador de Reportes Consolidados',
                                content: 'Presiona este botón para abrir el configurador de filtros de informes oficiales imprimibles en PDF.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalReporteMantenimiento"]')
                            },
                            {
                                target: '#modalReporteMantenimiento .modal-content',
                                title: 'Filtros del Reporte en Modal',
                                content: 'Esta ventana permite parametrizar el informe. Si no aplicas ningún filtro, el sistema emitirá el consolidado general de todos los registros.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalReporteMantenimiento'),
                                action: async () => {
                                    const modalEl = document.getElementById('modalReporteMantenimiento');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#modalReporteMantenimiento #placa',
                                title: 'Filtro por Vehículo',
                                content: 'Permite auditar el historial de mantenimiento exclusivo de una placa vehicular en particular.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalReporteMantenimiento #placa')
                            },
                            {
                                target: '#modalReporteMantenimiento #estado',
                                title: 'Filtro por Estado',
                                content: 'Selecciona entre órdenes en proceso (Activo) o culminadas con costo liquidado (Finalizado).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalReporteMantenimiento #estado')
                            },
                            {
                                target: '#modalReporteMantenimiento #cod_taller',
                                title: 'Filtro por Taller',
                                content: 'Permite totalizar las reparaciones canalizadas con un taller aliado determinado.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalReporteMantenimiento #cod_taller')
                            },
                            {
                                target: '#modalReporteMantenimiento #costo_base_desde',
                                title: 'Rango de Presupuestos',
                                content: 'Filtra órdenes cuyo presupuesto esté dentro de un rango monetario mínimo y máximo.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalReporteMantenimiento #costo_base_desde')
                            },
                            {
                                target: '#modalReporteMantenimiento button[type="submit"]',
                                title: 'Generar e Imprimir PDF',
                                content: 'Abre el documento formal en una pestaña nueva con membrete oficial, listo para firmar o archivar.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalReporteMantenimiento button[type="submit"]')
                            },
                            {
                                target: '#modalReporteMantenimiento button[data-bs-dismiss="modal"]',
                                title: 'Cerrar Modal',
                                content: 'Cierra el configurador y te devuelve a la tabla principal.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalReporteMantenimiento button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalReporteMantenimiento');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: 'a[href*="ver_recibo"]',
                                title: 'Recibo Digital Individual',
                                content: 'Para las órdenes finalizadas, este botón azul despliega el recibo individual de entrega con los costos desglosados.',
                                placement: 'left',
                                condition: () => !!document.querySelector('a[href*="ver_recibo"]')
                            },
                            {
                                target: null,
                                title: '¡Reportes y Recibos Dominados!',
                                content: 'Ahora conoces todas las alternativas para auditar y documentar los mantenimientos vehiculares.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 4. SERVICIOS TÉCNICOS
            // ==================================================================
            servicios: {
                nombre: 'Servicios Técnicos',
                icono: 'bi-car-front-fill',
                ruta: '/servicios',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Conocer el módulo',
                        icono: 'bi-info-circle',
                        descripcion: 'Servicios de embellecimiento, costos base/final y control de estados.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Inventario de Servicios Técnicos',
                                content: 'Controla servicios especializados como pulitura, limpieza de tapicería, alineación y lavado de motor para los vehículos.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaServicios',
                                title: 'Tabla de Servicios',
                                content: 'Permite buscar por servicio o placa, y consultar costos asociados en tiempo real.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaServicios thead',
                                title: 'Columnas Principales',
                                content: 'Muestra ID, nombre del servicio, estado, costo base proyectado, costo final real, fecha de realización y placa asignada.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaServicios tbody tr td .badge',
                                title: 'Estados Operativos',
                                content: 'Activo indica un servicio en proceso en taller. Finalizado indica que el trabajo concluyó y cuenta con comprobante.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaServicios tbody tr td .badge')
                            },
                            {
                                target: '.btn-finalizar-servicio',
                                title: 'Finalización del Servicio',
                                content: 'Disponible para servicios activos con vehículo: permite asentar el monto definitivo liquidado y emitir recibo.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-finalizar-servicio')
                            },
                            {
                                target: 'button[data-bs-target="#modalReporteServicios"]',
                                title: 'Reporte General de Servicios',
                                content: 'Permite generar reportes consolidados exportables en PDF, Excel y Word.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalReporteServicios"]')
                            },
                            {
                                target: null,
                                title: 'Resumen de Servicios',
                                content: 'Puedes iniciar los recorridos "Registrar Servicio" o "Recibos y Reportes" para conocer el flujo detallado.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un servicio',
                        icono: 'bi-plus-circle',
                        ruta: '/servicios/nuevo',
                        descripcion: 'Paso a paso en el formulario: asignación de vehículo, tipo de servicio, costos y fechas.',
                        pasos: [
                            {
                                target: '.card-body',
                                title: 'Formulario de Alta de Servicio',
                                content: 'Esta pantalla permite programar o registrar un servicio técnico o estético para un vehículo de la flota.',
                                placement: 'bottom'
                            },
                            {
                                target: '#placa',
                                title: 'Vehículo a Intervenir (Obligatorio)',
                                content: 'Selecciona la placa del vehículo que recibirá el acondicionamiento.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('placa')
                            },
                            {
                                target: '#nombre_servicio',
                                title: 'Nombre del Servicio (Obligatorio)',
                                content: 'Ingresa la denominación clara del trabajo a realizar (ej: Pulitura general, Limpieza profunda de tapicería, Cambio de bujías).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre_servicio')
                            },
                            {
                                target: '#costo_base',
                                title: 'Costo Base Proyectado ($)',
                                content: 'Presupuesto base estimado en dólares para la ejecución del servicio.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('costo_base')
                            },
                            {
                                target: '#costo_final',
                                title: 'Costo Final ($) (Opcional)',
                                content: 'Puede llenarse si el trabajo ya fue culminado y se conoce el valor exacto facturado.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('costo_final')
                            },
                            {
                                target: '#fecha_realizacion',
                                title: 'Fecha de Realización (Obligatorio)',
                                content: 'Indica la fecha en que se llevará a cabo o concluyó el servicio.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('fecha_realizacion')
                            },
                            {
                                target: '#descripcion_especifica',
                                title: 'Descripción Específica (Obligatorio)',
                                content: 'Detalla las especificaciones técnicas, insumos requeridos o zonas del vehículo tratadas.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('descripcion_especifica')
                            },
                            {
                                target: 'button[type="submit"]',
                                title: 'Guardar Servicio',
                                content: 'Valida los datos y registra la orden de servicio en el sistema. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"]')
                            },
                            {
                                target: 'a.btn-secondary',
                                title: 'Cancelar y Regresar',
                                content: 'Descarta los cambios y regresa al inventario de servicios.',
                                placement: 'top',
                                condition: () => !!document.querySelector('a.btn-secondary')
                            },
                            {
                                target: null,
                                title: '¡Guía de Registro Finalizada!',
                                content: 'Has aprendido a usar el formulario real de servicios técnicos y sus restricciones.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    },
                    finalizar_reporte: {
                        id: 'finalizar_reporte',
                        nombre: 'Recibos y reportes en PDF',
                        icono: 'bi-file-earmark-text',
                        descripcion: 'Finalización de trabajos, recibo imprimible y reporte consolidado.',
                        pasos: [
                            {
                                target: '.btn-finalizar-servicio',
                                title: 'Finalizar Servicio',
                                content: 'En servicios activos con placa, este botón abre el modal para asentar el costo definitivo y culminar la orden.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-finalizar-servicio')
                            },
                            {
                                target: 'a[href*="ver_recibo_servicio"]',
                                title: 'Recibo Digital con Código',
                                content: 'En servicios finalizados, este botón permite visualizar e imprimir el comprobante detallado con sello digital y costos.',
                                placement: 'left',
                                condition: () => !!document.querySelector('a[href*="ver_recibo_servicio"]')
                            },
                            {
                                target: 'button[data-bs-target="#modalReporteServicios"]',
                                title: 'Configurador de Reportes',
                                content: 'Abre la ventana modal para emitir el informe consolidado con filtros específicos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalReporteServicios"]')
                            },
                            {
                                target: '#modalReporteServicios .modal-content',
                                title: 'Filtros y Formatos de Descarga',
                                content: 'Permite filtrar por nombre de servicio, estado (Activo/Finalizado) o placa, y exportar a PDF, Excel o Word.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalReporteServicios'),
                                action: async () => {
                                    const modalEl = document.getElementById('modalReporteServicios');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#nombre_servicio_reporte',
                                title: 'Filtro por Tipo de Servicio',
                                content: 'Permite acotar el informe a un servicio particular (ej: Pulitura o Lavado).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre_servicio_reporte')
                            },
                            {
                                target: '#estado_reporte',
                                title: 'Filtro por Estado',
                                content: 'Separa los servicios en curso de aquellos ya concluidos con costo liquidado.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('estado_reporte')
                            },
                            {
                                target: '#placa_reporte',
                                title: 'Filtro por Vehículo',
                                content: 'Genera el historial de servicios realizados sobre una placa en particular.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('placa_reporte')
                            },
                            {
                                target: '#modalReporteServicios button.btn-danger',
                                title: 'Descarga en PDF',
                                content: 'Genera el informe formal en formato PDF listo para descargar e imprimir.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalReporteServicios button.btn-danger')
                            },
                            {
                                target: '#modalReporteServicios button.btn-success',
                                title: 'Descarga en Hoja de Cálculo (Excel)',
                                content: 'Exporta los datos en formato .xlsx para auditoría financiera y contabilidad.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalReporteServicios button.btn-success')
                            },
                            {
                                target: '#modalReporteServicios button[data-bs-dismiss="modal"]',
                                title: 'Cerrar Ventana',
                                content: 'Cierra el modal y te devuelve a la tabla principal.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalReporteServicios button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalReporteServicios');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Completado!',
                                content: 'Has conocido cómo cerrar servicios y emitir reportes formales en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 5. COMPRAS DE ACCESORIOS
            // ==================================================================
            compras: {
                nombre: 'Compras de Accesorios',
                icono: 'bi-bag-check-fill',
                ruta: '/compras',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Conocer compras e insumos',
                        icono: 'bi-info-circle',
                        descripcion: 'Historial de adquisiciones comerciales, proveedores y desglose de ítems.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Gestión de Compras',
                                content: 'Centraliza las compras de repuestos, lubricantes y accesorios con proveedores comerciales.',
                                placement: 'bottom'
                            },
                            {
                                target: '.table.table-hover',
                                title: 'Tabla de Compras',
                                content: 'Lista las órdenes de compra con código (#ID), fecha, proveedor, tipo de compra, total de ítems y estado.',
                                placement: 'top'
                            },
                            {
                                target: '.badge.bg-success, .badge.bg-danger',
                                title: 'Estados de Compra',
                                content: 'Completada (adquisición efectuada con stock actualizado) o Anulada (revocada por auditoría).',
                                placement: 'top',
                                condition: () => !!document.querySelector('.badge.bg-success, .badge.bg-danger')
                            },
                            {
                                target: 'a[href*="detalle"]',
                                title: 'Consulta de Detalle',
                                content: 'Permite inspeccionar cada insumo comprado, su costo unitario y cantidad recibida.',
                                placement: 'left',
                                condition: () => !!document.querySelector('a[href*="detalle"]')
                            },
                            {
                                target: null,
                                title: 'Resumen de Compras',
                                content: 'Puedes iniciar el recorrido "Registrar Compra" para conocer el flujo de abastecimiento.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar una compra',
                        icono: 'bi-plus-circle',
                        ruta: '/compras/nueva',
                        descripcion: 'Paso a paso en el formulario: proveedor, tipo de adquisición y observaciones.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Formulario de Nueva Compra',
                                content: 'Esta pantalla inicia una orden de compra para reponer materiales, repuestos o lubricantes para el concesionario.',
                                placement: 'bottom'
                            },
                            {
                                target: 'select[name="rif_proveedor"]',
                                title: 'Proveedor Comercial (Obligatorio)',
                                content: 'Selecciona la empresa proveedora que suministra los repuestos o insumos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('select[name="rif_proveedor"]')
                            },
                            {
                                target: 'a[href*="nuevo_proveedor"]',
                                title: 'Afiliación Rápida de Proveedores',
                                content: 'Si la empresa aún no está registrada, este enlace te permite darla de alta en el directorio comercial.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('a[href*="nuevo_proveedor"]')
                            },
                            {
                                target: 'select[name="tipo_compra"]',
                                title: 'Modalidad de la Compra',
                                content: 'Clasifica la orden: "Normal" (abastecimiento periódico), "Urgente" (requerimiento crítico inmediato) o "Mantenimiento" (consumibles específicos de taller).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('select[name="tipo_compra"]')
                            },
                            {
                                target: 'textarea[name="observaciones"]',
                                title: 'Observaciones de la Compra',
                                content: 'Campo de texto (hasta 100 caracteres) para notas de facturación, condiciones de entrega o número de cotización externa.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('textarea[name="observaciones"]')
                            },
                            {
                                target: '.alert.alert-info',
                                title: 'Flujo Asistido en Dos Pasos',
                                content: 'Una vez creada la compra, el sistema te redirige automáticamente al detalle para cargar los insumos adquiridos y sus costos.',
                                placement: 'top',
                                condition: () => !!document.querySelector('.alert.alert-info')
                            },
                            {
                                target: 'button[type="submit"]',
                                title: 'Botón Crear Compra',
                                content: 'Guarda la cabecera de la orden y habilita la pantalla para añadir ítems. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"]')
                            },
                            {
                                target: 'a.btn-secondary',
                                title: 'Cancelar Operación',
                                content: 'Regresa al listado general de compras sin guardar ningún cambio.',
                                placement: 'top',
                                condition: () => !!document.querySelector('a.btn-secondary')
                            },
                            {
                                target: null,
                                title: '¡Guía de Compra Finalizada!',
                                content: 'Has conocido el flujo de abastecimiento comercial de insumos y repuestos.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 6. INSUMOS DE VEHÍCULOS
            // ==================================================================
            insumos: {
                nombre: 'Insumos de Vehículos',
                icono: 'bi-box-seam-fill',
                ruta: '/insumos',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Control de inventario de insumos',
                        icono: 'bi-info-circle',
                        descripcion: 'Existencias, niveles de alerta (agotado/bajo) y edición.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Control de Insumos',
                                content: 'Supervisa las existencias de materiales, lubricantes y repuestos utilizados en el taller.',
                                placement: 'bottom'
                            },
                            {
                                target: '.table.table-hover',
                                title: 'Tabla de Existencias',
                                content: 'Muestra el código, denominación, descripción técnica, cantidad actual y semáforo de disponibilidad.',
                                placement: 'top'
                            },
                            {
                                target: '.badge.bg-success, .badge.bg-warning, .badge.bg-danger',
                                title: 'Semáforo de Stock',
                                content: 'Verde: Stock normal. Amarillo: Stock bajo (5 o menos unidades). Rojo: Agotado (requiere compra inmediata).',
                                placement: 'top',
                                condition: () => !!document.querySelector('.badge.bg-success, .badge.bg-warning, .badge.bg-danger')
                            },
                            {
                                target: 'a[href*="nuevo"]',
                                title: 'Registrar Nuevo Insumo',
                                content: 'Permite incorporar nuevos ítems al catálogo de inventario con su stock inicial.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('a[href*="nuevo"]')
                            },
                            {
                                target: null,
                                title: '¡Recorrido Concluido!',
                                content: 'Has conocido cómo monitorear los niveles de insumos del taller.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un insumo',
                        icono: 'bi-plus-circle',
                        ruta: '/insumos/nuevo',
                        descripcion: 'Paso a paso en el formulario: denominación, descripción y stock inicial.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Alta de Nuevo Insumo',
                                content: 'Esta pantalla permite incorporar un nuevo tipo de material, lubricante o repuesto al catálogo del taller.',
                                placement: 'bottom'
                            },
                            {
                                target: 'input[name="nombre"]',
                                title: 'Nombre del Insumo (Obligatorio)',
                                content: 'Ingresa la denominación clara del material (ej: Aceite 20W50, Filtro de Aire, Jabón Espumoso).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="nombre"]')
                            },
                            {
                                target: 'textarea[name="descripcion"]',
                                title: 'Descripción Técnica (Opcional)',
                                content: 'Detalla especificaciones técnicas, viscosidad, compatibilidad o recomendaciones de uso.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('textarea[name="descripcion"]')
                            },
                            {
                                target: 'input[name="stock"]',
                                title: 'Stock Inicial en Almacén',
                                content: 'Cantidad física disponible al momento de crear el registro (mínimo 0 unidades).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="stock"]')
                            },
                            {
                                target: '.alert.alert-info',
                                title: 'Actualización Dinámica de Stock',
                                content: 'El stock aumentará automáticamente cuando se registren compras de este insumo y disminuirá con los servicios o mantenimientos.',
                                placement: 'top',
                                condition: () => !!document.querySelector('.alert.alert-info')
                            },
                            {
                                target: 'button[type="submit"]',
                                title: 'Botón Guardar Insumo',
                                content: 'Verifica los campos y registra el insumo en el inventario activo. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"]')
                            },
                            {
                                target: 'a.btn-secondary',
                                title: 'Botón Cancelar',
                                content: 'Descarta la operación y te regresa al inventario de insumos sin alterar datos.',
                                placement: 'top',
                                condition: () => !!document.querySelector('a.btn-secondary')
                            },
                            {
                                target: null,
                                title: '¡Guía de Insumo Finalizada!',
                                content: 'Has aprendido cómo incorporar insumos y materiales al catálogo de AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 7. INVENTARIO DE VEHÍCULOS
            // ==================================================================
            vehiculos: {
                nombre: 'Inventario de Vehículos',
                icono: 'bi-car-front',
                ruta: '/vehiculos-lista',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Conocer el inventario',
                        icono: 'bi-info-circle',
                        descripcion: 'Tabla de unidades, estados (Disponible, Vendido, Mantenimiento) y acciones.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Inventario Central de Flota',
                                content: 'Este panel agrupa todos los vehículos registrados en la flota de AutoMall.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaVehiculos',
                                title: 'Tabla de Vehículos',
                                content: 'Consulta unidades por placa, marca, modelo, año, kilometraje o estado con DataTables.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaVehiculos tbody tr td .badge',
                                title: 'Estados de Unidad',
                                content: 'Disponible (listo para catálogo o venta), Mantenimiento (en acondicionamiento técnico) y Vendido (transacción cerrada).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaVehiculos tbody tr td .badge')
                            },
                            {
                                target: '[data-bs-target="#modalGaleriaFotos"]',
                                title: 'Galería de Fotografías',
                                content: 'Haz clic en la imagen miniatura para abrir el carrusel completo de fotos en alta resolución.',
                                placement: 'right',
                                condition: () => !!document.querySelector('[data-bs-target="#modalGaleriaFotos"]')
                            },
                            {
                                target: '[data-bs-target="#modalDetalles"]',
                                title: 'Expediente Completo',
                                content: 'Despliega la ficha con documentación, accesorios, kilometraje y observaciones técnicas.',
                                placement: 'left',
                                condition: () => !!document.querySelector('[data-bs-target="#modalDetalles"]')
                            },
                            {
                                target: 'a[href*="vehiculos/editar"]',
                                title: 'Edición de Unidad',
                                content: 'Permite actualizar kilometraje, color, precio de venta o documentación adjunta.',
                                placement: 'left',
                                condition: () => !!document.querySelector('a[href*="vehiculos/editar"]')
                            },
                            {
                                target: null,
                                title: 'Resumen del Inventario',
                                content: 'Puedes iniciar el recorrido "Cómo Registrar un Vehículo" para conocer los requisitos de ingreso.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un vehículo',
                        icono: 'bi-plus-circle',
                        ruta: '/vehiculos-registrar',
                        descripcion: 'Paso a paso en el formulario: documentación, ficha técnica, accesorios, fotos y precio.',
                        pasos: [
                            {
                                target: '.card-body',
                                title: 'Formulario de Ingreso de Vehículo',
                                content: 'Este formulario integral registra tanto la documentación legal como las especificaciones técnicas del vehículo que ingresa al concesionario.',
                                placement: 'bottom'
                            },
                            {
                                target: 'input[name="fecha_ingreso"]',
                                title: 'Fecha de Ingreso (Obligatorio)',
                                content: 'Indica el día exacto en que la unidad entra al concesionario o patio de exhibición.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="fecha_ingreso"]')
                            },
                            {
                                target: '#original_totalPropiedad',
                                title: 'Documentación Legal Recibida',
                                content: 'Verifica los recaudos físicos disponibles mediante los switches: Título de Propiedad, Experticia de Tránsito, Carnet de Circulación, Finiquito y Póliza.',
                                placement: 'right',
                                condition: () => !!document.getElementById('original_totalPropiedad')
                            },
                            {
                                target: '#copia_llaves',
                                title: 'Accesorios y Equipamiento',
                                content: 'Marca los implementos entregados con el auto: copia de llaves, caucho de repuesto y triángulo de seguridad.',
                                placement: 'right',
                                condition: () => !!document.getElementById('copia_llaves')
                            },
                            {
                                target: 'textarea[name="otro_documento"]',
                                title: 'Observaciones Legales Extra',
                                content: 'Campo para detallar documentos pendientes, poderes especiales o notas de consignación.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('textarea[name="otro_documento"]')
                            },
                            {
                                target: 'input[name="placa"]',
                                title: 'Placa o Matrícula (Obligatorio)',
                                content: 'Identificador único vehicular (ej: ABC-123). No puede repetirse con ningún auto ya registrado.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="placa"]')
                            },
                            {
                                target: 'input[name="color"]',
                                title: 'Color de la Carrocería',
                                content: 'Indica la tonalidad oficial registrada en el carnet de circulación (ej: Blanco, Plata, Azul marino).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="color"]')
                            },
                            {
                                target: 'input[name="anio"]',
                                title: 'Año del Modelo',
                                content: 'Año de fabricación del vehículo (ej: 2022).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="anio"]')
                            },
                            {
                                target: 'input[name="kilometraje"]',
                                title: 'Kilometraje Recorrido',
                                content: 'Lectura del odómetro al momento de la recepción física.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="kilometraje"]')
                            },
                            {
                                target: '#select-modelo',
                                title: 'Modelo y Fabricante',
                                content: 'Al seleccionar el modelo, el sistema detecta y enlaza automáticamente la marca correspondiente.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('select-modelo')
                            },
                            {
                                target: 'select[name="cedula"]',
                                title: 'Propietario o Consignatario',
                                content: 'Selecciona al dueño legal anterior o consignatario responsable de la unidad.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('select[name="cedula"]')
                            },
                            {
                                target: '#input-imagenes',
                                title: 'Galería de Fotografías',
                                content: 'Puedes seleccionar varias imágenes a la vez (Ctrl/Shift) para generar la vitrina y ficha técnica.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('input-imagenes')
                            },
                            {
                                target: 'input[name="precio"]',
                                title: 'Precio de Venta ($)',
                                content: 'Fija el valor comercial en dólares acordado para la publicación en catálogo.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="precio"]')
                            },
                            {
                                target: 'textarea[name="descripcion_catalogo"]',
                                title: 'Descripción Comercial para Clientes',
                                content: 'Texto descriptivo que se mostrará en el escaparate: estado de tapicería, extras, historial de servicio y comodidades.',
                                placement: 'top',
                                condition: () => !!document.querySelector('textarea[name="descripcion_catalogo"]')
                            },
                            {
                                target: 'button[type="submit"]',
                                title: 'Finalizar Registro',
                                content: 'Valida todos los campos y asienta el vehículo con estatus "Disponible" en la flota. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"]')
                            },
                            {
                                target: 'a.btn-outline-secondary',
                                title: 'Cancelar',
                                content: 'Descarta la información digitada y regresa al inventario general.',
                                placement: 'top',
                                condition: () => !!document.querySelector('a.btn-outline-secondary')
                            },
                            {
                                target: null,
                                title: '¡Guía de Registro Vehicular Finalizada!',
                                content: 'Has conocido en profundidad el proceso de ingreso y documentación vehicular en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 8. CATÁLOGO COMERCIAL
            // ==================================================================
            catalogo: {
                nombre: 'Catálogo Comercial',
                icono: 'bi-grid-fill',
                ruta: '/catalogo-ventas',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Exploración del catálogo',
                        icono: 'bi-search',
                        descripcion: 'Vehículos en exhibición, precios comerciales y expediente de venta.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Vehículos en Exhibición Comercial',
                                content: 'Muestra las unidades que cumplen las condiciones para oferta comercial activa al cliente.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaCatalogo',
                                title: 'Tabla Comercial',
                                content: 'Permite ordenar por precio, año y marca para agilizar la atención a compradores.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaCatalogo .text-success',
                                title: 'Precios en Divisa ($)',
                                content: 'Cada unidad refleja su cotización de venta fijada por la gerencia comercial.',
                                placement: 'left',
                                condition: () => !!document.querySelector('#tablaCatalogo .text-success')
                            },
                            {
                                target: '[data-bs-target="#modalDetalles"]',
                                title: 'Ficha de Presentación',
                                content: 'Abre el expediente listo para imprimir o mostrar al cliente durante una cita comercial.',
                                placement: 'left',
                                condition: () => !!document.querySelector('[data-bs-target="#modalDetalles"]')
                            },
                            {
                                target: null,
                                title: '¡Catálogo Comercial Exploratado!',
                                content: 'Has conocido las herramientas de exhibición y venta vehicular.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 9. MARCAS DE VEHÍCULOS
            // ==================================================================
            marcas: {
                nombre: 'Marcas de Vehículos',
                icono: 'bi-tag-fill',
                ruta: '/marcas/registro',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Gestión de marcas fabricantes',
                        icono: 'bi-info-circle',
                        descripcion: 'Registro de fabricantes, unicidad y listado activo.',
                        pasos: [
                            {
                                target: '.card-header.bg-primary',
                                title: 'Alta de Marcas',
                                content: 'Permite registrar nuevos fabricantes en el sistema (ej: Toyota, Chevrolet, Hyundai).',
                                placement: 'bottom'
                            },
                            {
                                target: '#nombre_marca',
                                title: 'Nombre de la Marca',
                                content: 'Ingresa la denominación oficial. El sistema valida que no exista previamente.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre_marca')
                            },
                            {
                                target: '#tablaMarcas',
                                title: 'Marcas Registradas',
                                content: 'Tabla con las marcas activas disponibles para enlazar a modelos y vehículos.',
                                placement: 'top',
                                condition: () => !!document.getElementById('tablaMarcas')
                            },
                            {
                                target: null,
                                title: '¡Módulo de Marcas Completado!',
                                content: 'Has aprendido cómo administrar las marcas del ecosistema AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 10. MODELOS DE VEHÍCULOS
            // ==================================================================
            modelos: {
                nombre: 'Modelos de Vehículos',
                icono: 'bi-diagram-3-fill',
                ruta: '/modelos/registro',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Gestión de modelos',
                        icono: 'bi-info-circle',
                        descripcion: 'Vinculación de modelos con su marca fabricante correspondiente.',
                        pasos: [
                            {
                                target: '.card-header.bg-primary',
                                title: 'Alta de Modelos',
                                content: 'Permite registrar líneas y modelos vehiculares vinculados a una marca.',
                                placement: 'bottom'
                            },
                            {
                                target: '#cod_marca',
                                title: 'Selección de Marca Fabricante',
                                content: 'Debes elegir la marca a la cual pertenece el nuevo modelo.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('cod_marca')
                            },
                            {
                                target: '#nombre_modelo',
                                title: 'Nombre del Modelo',
                                content: 'Ingresa el modelo (ej: Corolla, Cruze, Tucson). Máximo 21 caracteres.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre_modelo')
                            },
                            {
                                target: '#tablaModelos',
                                title: 'Modelos en Sistema',
                                content: 'Inventario con los modelos disponibles para seleccionar al registrar vehículos.',
                                placement: 'top',
                                condition: () => !!document.getElementById('tablaModelos')
                            },
                            {
                                target: null,
                                title: '¡Modelos Completado!',
                                content: 'Has aprendido cómo registrar y estructurar los modelos vehiculares.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 11. HISTORIAL DE VEHÍCULOS
            // ==================================================================
            historial_vehiculos: {
                nombre: 'Historial de Flota',
                icono: 'bi-clock-history',
                ruta: '/vehiculos-historial',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Trazabilidad de la flota',
                        icono: 'bi-info-circle',
                        descripcion: 'Auditoría cronológica de cambios de estado y transiciones operativas.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Historial de Movimientos',
                                content: 'Audita cada cambio de estado experimentado por los vehículos desde su ingreso.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaHistorial',
                                title: 'Registro Cronológico',
                                content: 'Muestra fecha y hora exacta, placa, vehículo, estado asignado y observaciones registradas.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaHistorial thead',
                                title: 'Trazabilidad Inmutable',
                                content: 'Permite reconstruir el ciclo de vida de cada unidad: ingreso, paso a taller, exhibición y venta.',
                                placement: 'bottom'
                            },
                            {
                                target: null,
                                title: '¡Trazabilidad Comprendida!',
                                content: 'Has aprendido cómo auditar los movimientos de la flota vehicular.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 12. GESTIÓN DE CITAS
            // ==================================================================
            citas: {
                nombre: 'Gestión de Citas',
                icono: 'bi-calendar-event',
                ruta: '/consultar',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Consultar citas agendadas',
                        icono: 'bi-info-circle',
                        descripcion: 'Listado de citas, estados (Pendiente, Finalizada, Cancelada) y placa.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Gestión de Citas',
                                content: 'Coordina visitas de inspección y citas de prueba con compradores potenciales.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaCitas',
                                title: 'Agenda de Citas',
                                content: 'Consulta fecha, hora, estado, marca, modelo, placa del auto y cliente asignado.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaCitas tbody tr td .badge',
                                title: 'Estados de la Cita',
                                content: 'Pendiente (programada por realizar), Finalizada (visita completada) o Cancelada.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaCitas tbody tr td .badge')
                            },
                            {
                                target: 'a[href*="agendar"]',
                                title: 'Agendar Nueva Cita',
                                content: 'Acceso al formulario para concertar una nueva cita con cliente y vehículo seleccionado.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('a[href*="agendar"]')
                            },
                            {
                                target: null,
                                title: '¡Citas Explicadas!',
                                content: 'Puedes iniciar el recorrido "Cómo agendar una cita" para aprender a reservar horarios.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    agendar: {
                        id: 'agendar',
                        nombre: 'Cómo agendar una cita',
                        icono: 'bi-plus-circle',
                        ruta: '/agendar',
                        descripcion: 'Paso a paso en el formulario: fecha, hora, cliente y selección de vehículo.',
                        pasos: [
                            {
                                target: '.card-registro',
                                title: 'Formulario de Agenda de Cita',
                                content: 'Esta pantalla programa una cita de inspección vehicular para clientes interesados en adquirir una unidad.',
                                placement: 'bottom'
                            },
                            {
                                target: '#fecha_cita',
                                title: 'Fecha de la Cita (Obligatorio)',
                                content: 'Haz clic para seleccionar el día en el calendario interactivo. No se admiten fechas pasadas.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('fecha_cita')
                            },
                            {
                                target: '#hora_cita',
                                title: 'Hora de la Cita (Obligatorio)',
                                content: 'El horario de atención al cliente está restringido estrictamente entre las 8:00 AM y las 6:00 PM (18:00).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('hora_cita')
                            },
                            {
                                target: '#select-cliente',
                                title: 'Selección de Cliente',
                                content: 'Elige el comprador que asistirá a la cita. Si eres cliente particular, el sistema te asigna de forma automática.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('select-cliente')
                            },
                            {
                                target: '#select-vehiculo',
                                title: 'Vehículo del Catálogo',
                                content: 'Selecciona la unidad que el comprador desea inspeccionar o probar físicamente.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('select-vehiculo')
                            },
                            {
                                target: '#contenedor-previsualizacion',
                                title: 'Previsualización Automática',
                                content: 'Al elegir un vehículo, este recuadro despliega al instante su fotografía y especificaciones principales.',
                                placement: 'left',
                                condition: () => !!document.getElementById('contenedor-previsualizacion')
                            },
                            {
                                target: '#btn-agendar',
                                title: 'Confirmar Cita',
                                content: 'Registra la cita en estado "Pendiente" y bloquea el horario para evitar colisiones de agenda. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.getElementById('btn-agendar')
                            },
                            {
                                target: null,
                                title: '¡Guía de Citas Finalizada!',
                                content: 'Has conocido cómo programar y reservar citas de inspección en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 13. VENTA DE VEHÍCULOS
            // ==================================================================
            ventas: {
                nombre: 'Venta de Vehículos',
                icono: 'bi-cash-stack',
                ruta: '/ventas/lista_ventas',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Historial de operaciones de venta',
                        icono: 'bi-info-circle',
                        descripcion: 'Buscador por placa, modalidades (Contado/Crédito) y saldos.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Historial de Ventas',
                                content: 'Supervisa las operaciones comerciales de venta de unidades y su estado de amortización.',
                                placement: 'bottom'
                            },
                            {
                                target: '#inputPlaca',
                                title: 'Filtro por Placa',
                                content: 'Escribe cualquier placa para encontrar al instante la venta y su expediente financiero.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('inputPlaca')
                            },
                            {
                                target: '#tablaVentas',
                                title: 'Tabla de Ventas',
                                content: 'Refleja código (#ID), fecha, cliente, auto, modalidad comercial, deuda total, último abono y saldo pendiente.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaVentas .badge.bg-info, #tablaVentas .badge.bg-primary',
                                title: 'Modalidad Comercial',
                                content: 'Contado: liquidado al momento. Crédito: financiamiento con control de cuotas y abonos pendientes.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaVentas .badge.bg-info, #tablaVentas .badge.bg-primary')
                            },
                            {
                                target: 'a[href*="vista_registro"]',
                                title: 'Registrar Nueva Venta',
                                content: 'Acceso al proceso asistido de facturación y formalización de venta con generación de factura en PDF.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('a[href*="vista_registro"]')
                            },
                            {
                                target: null,
                                title: '¡Ventas Comprendidas!',
                                content: 'Has conocido cómo monitorear las transacciones comerciales de AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar una venta',
                        icono: 'bi-plus-circle',
                        ruta: '/ventas/registrar_venta',
                        descripcion: 'Paso a paso en el asistente: cliente, selección de vehículo, financiamiento y factura PDF.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Asistente de Ventas y Facturación',
                                content: 'Este proceso guiado formaliza la venta legal de un vehículo, calculando importes en divisas y bolívares según la tasa BCV oficial.',
                                placement: 'bottom'
                            },
                            {
                                target: '#step-1',
                                title: 'Paso 1: Identificación del Comprador',
                                content: 'El primer paso del proceso asocia o registra al cliente que adquiere el vehículo.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('step-1')
                            },
                            {
                                target: '#buscar_cliente',
                                title: 'Buscador en Tiempo Real',
                                content: 'Permite buscar clientes registrados escribiendo su cédula de identidad, RIF o nombre.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('buscar_cliente')
                            },
                            {
                                target: '#select_cliente_lista',
                                title: 'Selector de Clientes Registrados',
                                content: 'Alternativamente, puedes desplegar la lista completa de clientes activos en el sistema.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('select_cliente_lista')
                            },
                            {
                                target: '#vista_previa_cliente',
                                title: 'Ficha de Comprobación del Comprador',
                                content: 'Verifica los nombres, teléfono, correo y dirección residencial antes de continuar.',
                                placement: 'left',
                                condition: () => !!document.getElementById('vista_previa_cliente')
                            },
                            {
                                target: '#btn_ir_paso_2',
                                title: 'Avanzar al Paso 2',
                                content: 'Presiona este botón para validar al cliente y pasar a la selección del vehículo.',
                                placement: 'left',
                                condition: () => !!document.getElementById('btn_ir_paso_2')
                            },
                            {
                                target: '#step-2, #buscar_placa',
                                title: 'Paso 2: Selección del Vehículo',
                                content: 'Permite buscar por placa o seleccionar del inventario de unidades disponibles en venta.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('buscar_placa') || !!document.getElementById('step-2')
                            },
                            {
                                target: '#tiene_poder, #traspaso_papel',
                                title: 'Garantías y Legalidad de Venta',
                                content: 'Verifica que la unidad cuente con poder notariado y documentación de traspaso lista.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('tiene_poder')
                            },
                            {
                                target: '#btn_ir_paso_3',
                                title: 'Avanzar al Paso 3: Financiamiento',
                                content: 'Verifica el precio y pasa a definir la modalidad comercial de pago.',
                                placement: 'left',
                                condition: () => !!document.getElementById('btn_ir_paso_3')
                            },
                            {
                                target: '#tipo_operacion',
                                title: 'Modalidad Comercial',
                                content: 'Selecciona "Contado" para cancelación total o "Crédito" para amortización por cuotas con abonos.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('tipo_operacion')
                            },
                            {
                                target: '#cod_metodo',
                                title: 'Método o Pasarela de Pago',
                                content: 'Elige la forma de cobro: Pago Móvil, Transferencia bancaria, Divisas en efectivo o plataforma digital.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('cod_metodo')
                            },
                            {
                                target: '#cod_moneda',
                                title: 'Moneda de Recepción',
                                content: 'Divisa en la que se registra la transacción (Dólares $, Bolívares Bs, etc.).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('cod_moneda')
                            },
                            {
                                target: '#cod_banco',
                                title: 'Banco Receptor Corporativo',
                                content: 'Cuenta bancaria de AutoMall receptora de los fondos.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('cod_banco')
                            },
                            {
                                target: null,
                                title: 'Factura Digital en PDF y Culminación',
                                content: 'Al presionar "Procesar y Emitir Factura", el sistema descuenta el auto del inventario a estado "Vendido" y genera la factura legal en PDF.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía de Ventas'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 14. GESTIÓN DE PAGOS
            // ==================================================================
            pagos: {
                nombre: 'Gestión de Pagos',
                icono: 'bi-credit-card',
                ruta: '/pagos',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Control y conciliación de abonos',
                        icono: 'bi-info-circle',
                        descripcion: 'Monitoreo de pagos, comprobantes bancarios y estados de cuenta.',
                        pasos: [
                            {
                                target: 'h4, h2',
                                title: 'Panel de Pagos y Abonos',
                                content: 'Gestiona la recaudación de cuotas de financiamiento y conciliación de transferencias bancarias.',
                                placement: 'bottom'
                            },
                            {
                                target: '#inputBuscarPlaca',
                                title: 'Búsqueda por Placa',
                                content: 'Filtra las transacciones registradas de un vehículo específico en tiempo real.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('inputBuscarPlaca')
                            },
                            {
                                target: '#tablaPagosBody, .table',
                                title: 'Movimientos de Pago',
                                content: 'Presenta el cliente, vehículo, monto abonado, referencia bancaria y estado de verificación.',
                                placement: 'top'
                            },
                            {
                                target: 'a[href*="registrar_pago"]',
                                title: 'Registrar Abono',
                                content: 'Permite cargar un comprobante de abono indicando fecha, banco, monto y número de referencia.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('a[href*="registrar_pago"]')
                            },
                            {
                                target: null,
                                title: '¡Gestión de Pagos Explicada!',
                                content: 'Has conocido cómo conciliar los pagos y mantener al día las cuentas por cobrar.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 15. CLIENTES
            // ==================================================================
            clientes: {
                nombre: 'Clientes',
                icono: 'bi-people',
                ruta: '/clientes',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Directorio de clientes',
                        icono: 'bi-info-circle',
                        descripcion: 'Fichas personales, datos de contacto y edición rápida.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Directorio de Clientes',
                                content: 'Centraliza los expedientes y datos de contacto de todos los clientes de AutoMall.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaClientes',
                                title: 'Tabla de Clientes',
                                content: 'Permite consultar cédula, nombres, teléfono, correo y dirección residencial con DataTables.',
                                placement: 'top'
                            },
                            {
                                target: '.btn-editar-cliente',
                                title: 'Edición Rápida en Modal',
                                content: 'Abre el formulario modal de modificación para actualizar teléfono, correo o dirección sin recargar la página.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-editar-cliente')
                            },
                            {
                                target: 'a[href*="registrar_clientes"]',
                                title: 'Registrar Nuevo Cliente',
                                content: 'Acceso al formulario integral para incorporar un nuevo cliente al directorio.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('a[href*="registrar_clientes"]')
                            },
                            {
                                target: null,
                                title: '¡Directorio de Clientes Comprendido!',
                                content: 'Has aprendido cómo gestionar los datos y expedientes de clientes.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un cliente',
                        icono: 'bi-plus-circle',
                        ruta: '/registrar_clientes',
                        descripcion: 'Paso a paso en el formulario: foto, cédula, nombres, contacto y credenciales.',
                        pasos: [
                            {
                                target: '.auth-card',
                                title: 'Formulario de Alta de Clientes',
                                content: 'Esta pantalla registra la cuenta de un nuevo comprador en AutoMall, habilitándolo para agendar citas y realizar compras.',
                                placement: 'bottom'
                            },
                            {
                                target: 'label[for="foto_perfil"]',
                                title: 'Fotografía de Perfil (Opcional)',
                                content: 'Haz clic en el botón de cámara para adjuntar una fotografía de perfil del cliente.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('label[for="foto_perfil"]')
                            },
                            {
                                target: '#cedula',
                                title: 'Cédula de Identidad (Obligatorio)',
                                content: 'Identificador legal del cliente. Máximo 10 caracteres numéricos sin puntos ni guiones.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('cedula')
                            },
                            {
                                target: '#nombre',
                                title: 'Nombre de Pila',
                                content: 'Ingresa el nombre o nombres legales del cliente.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre')
                            },
                            {
                                target: '#apellido',
                                title: 'Apellidos del Cliente',
                                content: 'Ingresa los apellidos completos.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('apellido')
                            },
                            {
                                target: '#telefono',
                                title: 'Teléfono Móvil (11 dígitos)',
                                content: 'Número de contacto directo con código de operadora (ej: 04141234567).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('telefono')
                            },
                            {
                                target: '#direccion',
                                title: 'Dirección de Residencia',
                                content: 'Ubicación física del cliente para expedientes de venta y contratos.',
                                placement: 'top',
                                condition: () => !!document.getElementById('direccion')
                            },
                            {
                                target: '#email',
                                title: 'Correo Electrónico',
                                content: 'Email corporativo o personal para recibir notificaciones de citas y facturas digitales.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('email')
                            },
                            {
                                target: '#password',
                                title: 'Contraseña de Acceso',
                                content: 'Clave confidencial para que el cliente ingrese al portal y consulte sus vehículos.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('password')
                            },
                            {
                                target: 'button[type="submit"]',
                                title: 'Registrarme como Cliente',
                                content: 'Verifica los campos y crea la cuenta en el sistema. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"]')
                            },
                            {
                                target: null,
                                title: '¡Registro de Cliente Finalizado!',
                                content: 'Has aprendido los requerimientos del formulario de clientes en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    },
                    edicion: {
                        id: 'edicion',
                        nombre: 'Cómo editar un cliente',
                        icono: 'bi-pencil',
                        descripcion: 'Modificación de teléfono, correo y dirección en el modal.',
                        pasos: [
                            {
                                target: '.btn-editar-cliente',
                                title: 'Botón de Modificación',
                                content: 'En la columna Acciones, este botón con ícono de lápiz carga la ficha del cliente en el modal de edición.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-editar-cliente')
                            },
                            {
                                target: '#modalEditarCliente .modal-content',
                                title: 'Ventana Modal de Edición',
                                content: 'Permite actualizar los datos del cliente sin alterar su historial de compras ni citas registradas.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalEditarCliente'),
                                action: async () => {
                                    const btn = document.querySelector('.btn-editar-cliente');
                                    const modalEl = document.getElementById('modalEditarCliente');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        if (btn) {
                                            const doc = document.getElementById('editar_cedula');
                                            const nom = document.getElementById('editar_nombre');
                                            const ape = document.getElementById('editar_apellido');
                                            const cor = document.getElementById('editar_correo');
                                            const tel = document.getElementById('editar_telefono');
                                            const dir = document.getElementById('editar_direccion');
                                            if (doc && !doc.value) doc.value = btn.dataset.cedula || 'V-00000000';
                                            if (nom && !nom.value) nom.value = btn.dataset.nombre || '';
                                            if (ape && !ape.value) ape.value = btn.dataset.apellido || '';
                                            if (cor && !cor.value) cor.value = btn.dataset.correo || '';
                                            if (tel && !tel.value) tel.value = btn.dataset.telefono || '';
                                            if (dir && !dir.value) dir.value = btn.dataset.direccion || '';
                                        }
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#editar_cedula',
                                title: 'Cédula (Bloqueada)',
                                content: 'El documento de identidad es inmutable para garantizar la integridad referencial y auditoría.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('editar_cedula')
                            },
                            {
                                target: '#editar_nombre',
                                title: 'Actualizar Nombres',
                                content: 'Corrige ortografía o nombres de la ficha.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('editar_nombre')
                            },
                            {
                                target: '#editar_correo',
                                title: 'Correo Electrónico Actualizado',
                                content: 'Nuevo buzón para envío de recibos y estados de cuenta.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('editar_correo')
                            },
                            {
                                target: '#editar_telefono',
                                title: 'Teléfono de Contacto',
                                content: 'Nuevo número telefónico asignado al cliente.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('editar_telefono')
                            },
                            {
                                target: '#editar_direccion',
                                title: 'Dirección Física',
                                content: 'Actualización del domicilio del comprador.',
                                placement: 'top',
                                condition: () => !!document.getElementById('editar_direccion')
                            },
                            {
                                target: '#modalEditarCliente button[type="submit"]',
                                title: 'Guardar Cambios',
                                content: 'Aplica las modificaciones de forma segura en la base de datos.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalEditarCliente button[type="submit"]')
                            },
                            {
                                target: '#modalEditarCliente button[data-bs-dismiss="modal"]',
                                title: 'Cancelar Edición',
                                content: 'Descarta cualquier modificación y cierra el modal.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalEditarCliente button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalEditarCliente');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Edición de Cliente Explicada!',
                                content: 'Has conocido cómo mantener al día el padrón de clientes en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 16. PROPIETARIOS
            // ==================================================================
            propietarios: {
                nombre: 'Propietarios',
                icono: 'bi-person-badge',
                ruta: '/propietarios/lista',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Gestión de consignatarios',
                        icono: 'bi-info-circle',
                        descripcion: 'Directorio de dueños y consignatarios de unidades vehiculares.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Listado de Propietarios',
                                content: 'Registra a los dueños y consignatarios que colocan sus vehículos para intermediación comercial en AutoMall.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaPropietarios',
                                title: 'Tabla de Propietarios',
                                content: 'Refleja cédula o RIF, razón social, correo de contacto, teléfono y dirección física.',
                                placement: 'top'
                            },
                            {
                                target: 'a[href*="propietarios/registro"]',
                                title: 'Agregar Propietario',
                                content: 'Permite afiliar nuevos propietarios para habilitar la consignación de nuevos vehículos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('a[href*="propietarios/registro"]')
                            },
                            {
                                target: null,
                                title: '¡Propietarios Comprendido!',
                                content: 'Has aprendido cómo registrar dueños y consignatarios de la flota.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un propietario',
                        icono: 'bi-plus-circle',
                        ruta: '/propietarios/registro',
                        descripcion: 'Paso a paso en el formulario: cédula/RIF, razón social, teléfonos y tipo.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Alta de Consignatario o Propietario',
                                content: 'Registra la identidad legal del dueño del vehículo que ingresa en consignación o venta.',
                                placement: 'bottom'
                            },
                            {
                                target: 'input[name="cedula"]',
                                title: 'Cédula o RIF (Obligatorio)',
                                content: 'Identificación tributaria o documento de identidad numérico.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="cedula"]')
                            },
                            {
                                target: 'input[name="razon_social"]',
                                title: 'Razón Social o Nombre Legal',
                                content: 'Nombre completo de la persona natural o denominación fiscal de la empresa propietaria.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="razon_social"]')
                            },
                            {
                                target: 'input[name="telefono"]',
                                title: 'Teléfono de Contacto',
                                content: 'Número telefónico para coordinar liquidaciones de venta y traspasos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="telefono"]')
                            },
                            {
                                target: 'input[name="correo"]',
                                title: 'Correo Electrónico',
                                content: 'Email para remitir comprobantes de pago de venta o rendición de cuentas.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="correo"]')
                            },
                            {
                                target: 'textarea[name="direccion"]',
                                title: 'Dirección Fiscal',
                                content: 'Ubicación física del consignatario.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('textarea[name="direccion"]')
                            },
                            {
                                target: 'select[name="tipo"]',
                                title: 'Tipo de Propietario',
                                content: 'Define si es "Persona Natural" o "Persona Jurídica".',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('select[name="tipo"]')
                            },
                            {
                                target: 'button[type="submit"]',
                                title: 'Finalizar Registro',
                                content: 'Guarda al propietario en el sistema para permitir registrar vehículos a su nombre. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"]')
                            },
                            {
                                target: 'a[href*="propietarios/lista"]',
                                title: 'Volver al Listado',
                                content: 'Descarta y te devuelve al padrón de propietarios.',
                                placement: 'top',
                                condition: () => !!document.querySelector('a[href*="propietarios/lista"]')
                            },
                            {
                                target: null,
                                title: '¡Guía de Propietarios Concluida!',
                                content: 'Has conocido cómo registrar propietarios en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 17. VENDEDORES
            // ==================================================================
            vendedores: {
                nombre: 'Vendedores',
                icono: 'bi-person-vcard',
                ruta: '/vendedores',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Equipo comercial',
                        icono: 'bi-info-circle',
                        descripcion: 'Asesores comerciales de venta, datos de contacto y estado.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Equipo de Vendedores',
                                content: 'Supervisa los asesores comerciales autorizados para concretar ventas y atender citas.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaVendedores',
                                title: 'Tabla de Asesores',
                                content: 'Refleja cédula, nombre, apellido, teléfono, correo institucional y estatus activo/inactivo.',
                                placement: 'top'
                            },
                            {
                                target: 'button[data-bs-target="#registrarModal"]',
                                title: 'Nuevo Vendedor',
                                content: 'Abre el formulario modal para dar de alta a un nuevo asesor en el equipo comercial.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#registrarModal"]')
                            },
                            {
                                target: null,
                                title: '¡Equipo Comercial Comprendido!',
                                content: 'Has conocido cómo supervisar a los asesores de venta.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un vendedor',
                        icono: 'bi-plus-circle',
                        descripcion: 'Paso a paso en el modal: datos de identidad, contacto, correo y clave.',
                        pasos: [
                            {
                                target: 'button[data-bs-target="#registrarModal"]',
                                title: 'Acceso al Formulario',
                                content: 'Presiona este botón para abrir la ventana modal de alta de vendedor.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#registrarModal"]')
                            },
                            {
                                target: '#registrarModal .modal-content',
                                title: 'Modal de Alta de Asesor',
                                content: 'Esta ventana permite afiliar a un nuevo vendedor asignándole automáticamente el rol comercial correspondiente.',
                                placement: 'center',
                                condition: () => !!document.getElementById('registrarModal'),
                                action: async () => {
                                    const modalEl = document.getElementById('registrarModal');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#registrarModal #cedula',
                                title: 'Cédula de Identidad (Obligatorio)',
                                content: 'Documento legal del vendedor. Debe ser numérico y no duplicado.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#registrarModal #cedula')
                            },
                            {
                                target: '#registrarModal #nombre',
                                title: 'Nombres del Asesor',
                                content: 'Nombres de pila del vendedor.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#registrarModal #nombre')
                            },
                            {
                                target: '#registrarModal #apellido',
                                title: 'Apellidos del Asesor',
                                content: 'Apellidos completos del vendedor.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#registrarModal #apellido')
                            },
                            {
                                target: '#registrarModal #telefono',
                                title: 'Teléfono Móvil',
                                content: 'Línea de contacto para asignación de citas y comisiones.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#registrarModal #telefono')
                            },
                            {
                                target: '#registrarModal #email',
                                title: 'Correo Institucional',
                                content: 'Dirección de correo para ingresar al sistema y recibir notificaciones.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#registrarModal #email')
                            },
                            {
                                target: '#registrarModal #password',
                                title: 'Contraseña de Acceso',
                                content: 'Clave confidencial del vendedor para su inicio de sesión.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#registrarModal #password')
                            },
                            {
                                target: '#registrarModal #direccion',
                                title: 'Dirección de Residencia',
                                content: 'Ubicación física del asesor.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#registrarModal #direccion')
                            },
                            {
                                target: '#registrarModal button[type="submit"]',
                                title: 'Finalizar Registro',
                                content: 'Valida los datos y registra al asesor en estado Activo. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#registrarModal button[type="submit"]')
                            },
                            {
                                target: '#registrarModal button[data-bs-dismiss="modal"]',
                                title: 'Cancelar',
                                content: 'Cierra el modal sin guardar datos.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#registrarModal button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('registrarModal');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Vendedor Registrado!',
                                content: 'Has conocido cómo incorporar nuevos asesores al equipo comercial.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 18. PROVEEDORES
            // ==================================================================
            proveedores: {
                nombre: 'Proveedores',
                icono: 'bi-building',
                ruta: '/compras/proveedores',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Directorio de empresas aliadas',
                        icono: 'bi-info-circle',
                        descripcion: 'Proveedores de repuestos, accesorios y lubricantes.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Proveedores Comerciales',
                                content: 'Directorio de empresas que suministran insumos y repuestos al taller y concesionario.',
                                placement: 'bottom'
                            },
                            {
                                target: '.table.table-hover',
                                title: 'Tabla de Proveedores',
                                content: 'Muestra RIF o cédula, razón social, teléfonos, correo comercial, dirección y estatus.',
                                placement: 'top'
                            },
                            {
                                target: 'a[href*="nuevo_proveedor"]',
                                title: 'Alta de Proveedor',
                                content: 'Permite registrar una nueva casa comercial proveedora de repuestos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('a[href*="nuevo_proveedor"]')
                            },
                            {
                                target: null,
                                title: '¡Proveedores Explicados!',
                                content: 'Has conocido cómo administrar los aliados comerciales de insumos.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un proveedor',
                        icono: 'bi-plus-circle',
                        ruta: '/compras/proveedor/nuevo',
                        descripcion: 'Paso a paso en el formulario: RIF, razón social, dirección, teléfono y correo.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Alta Comercial de Proveedor',
                                content: 'Esta pantalla formaliza el registro de una empresa distribuidora de lubricantes o repuestos.',
                                placement: 'bottom'
                            },
                            {
                                target: 'input[name="rif"]',
                                title: 'RIF o Cédula Fiscal (Obligatorio)',
                                content: 'Número de registro tributario comercial (ej: J-12345678).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="rif"]')
                            },
                            {
                                target: 'input[name="razon_social"]',
                                title: 'Razón Social de la Empresa',
                                content: 'Nombre legal de la compañía suministradora.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="razon_social"]')
                            },
                            {
                                target: 'textarea[name="direccion"]',
                                title: 'Dirección de la Sede',
                                content: 'Ubicación física de la distribuidora o almacén comercial.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('textarea[name="direccion"]')
                            },
                            {
                                target: 'input[name="telefono"]',
                                title: 'Teléfono de Contacto',
                                content: 'Línea telefónica comercial (solo dígitos numéricos).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="telefono"]')
                            },
                            {
                                target: 'input[name="correo"]',
                                title: 'Correo Electrónico',
                                content: 'Buzón de correo para cotizaciones y pedidos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('input[name="correo"]')
                            },
                            {
                                target: 'button[type="submit"]',
                                title: 'Guardar Proveedor',
                                content: 'Registra a la empresa para que aparezca disponible en el selector de nuevas compras. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"]')
                            },
                            {
                                target: 'a.btn-secondary',
                                title: 'Cancelar',
                                content: 'Descarta la operación y regresa al directorio comercial.',
                                placement: 'top',
                                condition: () => !!document.querySelector('a.btn-secondary')
                            },
                            {
                                target: null,
                                title: '¡Proveedor Registrado!',
                                content: 'Has conocido cómo afiliar nuevas empresas distribuidoras en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 19. GESTIÓN DE USUARIOS
            // ==================================================================
            usuarios: {
                nombre: 'Gestión de Usuarios',
                icono: 'bi-person-gear',
                ruta: '/usuarios',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Control de cuentas de acceso',
                        icono: 'bi-info-circle',
                        descripcion: 'Cuentas de usuario, roles de seguridad y administración de accesos.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Gestión de Cuentas de Acceso',
                                content: 'Control central de las cuentas del sistema, niveles jerárquicos y seguridad.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaUsuarios',
                                title: 'Tabla de Usuarios',
                                content: 'Muestra cédula de identidad, nombres, contacto, correo institucional y rol asignado.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaUsuarios tbody tr td .badge',
                                title: 'Roles del Sistema',
                                content: 'Superusuario (acceso irrestricto), Administrador (gestión operativa), Vendedor o Cliente.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaUsuarios tbody tr td .badge')
                            },
                            {
                                target: 'button[data-bs-target="#modalCrear"]',
                                title: 'Crear Nuevo Usuario',
                                content: 'Permite registrar una cuenta definiendo cédula, nombres, correo, rol y contraseña inicial con preguntas secretas.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalCrear"]')
                            },
                            {
                                target: '.btn-editar-usuario',
                                title: 'Modificar Cuenta',
                                content: 'Permite actualizar datos de contacto, rol o estado del usuario en el sistema.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-editar-usuario')
                            },
                            {
                                target: null,
                                title: '¡Gestión de Usuarios Comprendida!',
                                content: 'Has aprendido cómo administrar las cuentas de usuario de AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un usuario',
                        icono: 'bi-plus-circle',
                        descripcion: 'Paso a paso en el modal: cédula, nombres, rol, contraseña y foto.',
                        pasos: [
                            {
                                target: 'button[data-bs-target="#modalCrear"]',
                                title: 'Acceso al Formulario',
                                content: 'Presiona este botón para abrir la ventana modal de registro de usuario.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalCrear"]')
                            },
                            {
                                target: '#modalCrear .modal-content',
                                title: 'Ventana Modal de Alta',
                                content: 'Esta ventana permite afiliar una nueva cuenta interna en el sistema.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalCrear'),
                                action: async () => {
                                    const modalEl = document.getElementById('modalCrear');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#modalCrear #cedula',
                                title: 'Cédula de Identidad (Obligatorio)',
                                content: 'Identificador único de la cuenta. Debe ser numérico y no repetirse en el sistema.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrear #cedula')
                            },
                            {
                                target: '#modalCrear #nombre',
                                title: 'Nombre de Pila',
                                content: 'Ingresa los nombres del usuario.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrear #nombre')
                            },
                            {
                                target: '#modalCrear #apellido',
                                title: 'Apellidos',
                                content: 'Ingresa los apellidos del usuario.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrear #apellido')
                            },
                            {
                                target: '#modalCrear #telefono',
                                title: 'Teléfono de Contacto',
                                content: 'Número telefónico del titular de la cuenta.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrear #telefono')
                            },
                            {
                                target: '#modalCrear #email',
                                title: 'Correo Electrónico',
                                content: 'Email corporativo o personal para acceso al sistema y recuperación.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrear #email')
                            },
                            {
                                target: '#modalCrear #password',
                                title: 'Contraseña Inicial',
                                content: 'Clave de seguridad requerida para el primer inicio de sesión.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrear #password')
                            },
                            {
                                target: '#modalCrear #direccion',
                                title: 'Dirección Física',
                                content: 'Ubicación domiciliaria del usuario.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrear #direccion')
                            },
                            {
                                target: '#modalCrear #foto_perfil',
                                title: 'Fotografía de Perfil (Opcional)',
                                content: 'Permite adjuntar una foto para el avatar superior del navbar.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrear #foto_perfil')
                            },
                            {
                                target: '#modalCrear button[type="submit"]',
                                title: 'Guardar Usuario',
                                content: 'Crea la cuenta en el sistema de seguridad. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrear button[type="submit"]')
                            },
                            {
                                target: '#modalCrear button[data-bs-dismiss="modal"]',
                                title: 'Cancelar',
                                content: 'Cierra la ventana modal sin alterar datos.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrear button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalCrear');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Usuario Registrado!',
                                content: 'Has conocido cómo registrar cuentas en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    },
                    edicion: {
                        id: 'edicion',
                        nombre: 'Cómo editar un usuario',
                        icono: 'bi-pencil',
                        descripcion: 'Modificación de rol, contacto y estado en el modal.',
                        pasos: [
                            {
                                target: '.btn-editar-usuario',
                                title: 'Acceso a la Modificación',
                                content: 'En la columna Acciones, este botón con ícono de lápiz abre el modal de edición para el usuario seleccionado.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-editar-usuario')
                            },
                            {
                                target: '#modalEditar .modal-content',
                                title: 'Ventana Modal de Edición',
                                content: 'Permite actualizar datos de contacto, rol o estatus del usuario.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalEditar'),
                                action: async () => {
                                    const btn = document.querySelector('.btn-editar-usuario');
                                    const modalEl = document.getElementById('modalEditar');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        if (btn) {
                                            const doc = document.getElementById('editar_cedula');
                                            const nom = document.getElementById('editar_nombre');
                                            const ape = document.getElementById('editar_apellido');
                                            const cor = document.getElementById('editar_correo');
                                            const tel = document.getElementById('editar_telefono');
                                            const dir = document.getElementById('editar_direccion');
                                            if (doc && !doc.value) doc.value = btn.dataset.cedula || 'V-00000000';
                                            if (nom && !nom.value) nom.value = btn.dataset.nombre || '';
                                            if (ape && !ape.value) ape.value = btn.dataset.apellido || '';
                                            if (cor && !cor.value) cor.value = btn.dataset.correo || '';
                                            if (tel && !tel.value) tel.value = btn.dataset.telefono || '';
                                            if (dir && !dir.value) dir.value = btn.dataset.direccion || '';
                                        }
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#editar_cedula',
                                title: 'Cédula (Inmutable)',
                                content: 'La cédula se mantiene protegida contra escritura para preservar la bitácora y auditoría.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('editar_cedula')
                            },
                            {
                                target: '#editar_nombre',
                                title: 'Nombres',
                                content: 'Permite corregir o actualizar los nombres del usuario.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('editar_nombre')
                            },
                            {
                                target: '#editar_correo',
                                title: 'Correo Institucional',
                                content: 'Actualización del buzón de contacto.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('editar_correo')
                            },
                            {
                                target: '#editar_cod_rol',
                                title: 'Rol de Seguridad',
                                content: 'Permite modificar el perfil de acceso: Superusuario, Administrador, Vendedor o Cliente.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('editar_cod_rol')
                            },
                            {
                                target: '#modalEditar button[type="submit"]',
                                title: 'Guardar Cambios',
                                content: 'Aplica las modificaciones validadas en la cuenta.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalEditar button[type="submit"]')
                            },
                            {
                                target: '#modalEditar button[data-bs-dismiss="modal"]',
                                title: 'Cancelar',
                                content: 'Cierra el modal descartando cualquier edición.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalEditar button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalEditar');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Edición de Usuario Finalizada!',
                                content: 'Has conocido cómo modificar usuarios y sus privilegios jerárquicos.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 20. GESTIÓN DE PERMISOS
            // ==================================================================
            permisos: {
                nombre: 'Gestión de Permisos',
                icono: 'bi-shield-lock',
                ruta: '/gestionar',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Matriz granular de permisos por rol',
                        icono: 'bi-info-circle',
                        descripcion: 'Control de acceso granular (Crear, Leer, Actualizar, Borrar) por módulo.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Seguridad Basada en Roles (RBAC)',
                                content: 'El módulo de Permisos permite gestionar el control de acceso basado en roles para cada funcionalidad del sistema con granularidad de acciones.',
                                placement: 'bottom'
                            },
                            {
                                target: 'select[name="cod_rol"]',
                                title: 'Selector del Rol a Configurar',
                                content: 'Elige el perfil cuyos privilegios deseas inspeccionar o modificar. Al cambiar la selección, la matriz se actualiza automáticamente.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('select[name="cod_rol"]')
                            },
                            {
                                target: '#tablaPermisos',
                                title: 'Matriz Modular de Permisos',
                                content: 'Lista todos los módulos activos del sistema y los permisos que este rol tiene actualmente asignados.',
                                placement: 'top',
                                condition: () => !!document.getElementById('tablaPermisos')
                            },
                            {
                                target: '#tablaPermisos tbody tr td:nth-child(2)',
                                title: 'Permisos Activos',
                                content: 'Las etiquetas verdes reflejan las operaciones autorizadas: p_crear (alta), p_leer (consulta), p_actualizar (modificación) o p_eliminar (borrado).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaPermisos tbody tr td:nth-child(2)')
                            },
                            {
                                target: 'button[data-bs-target^="#modalModulo_"]',
                                title: 'Edición de Permisos por Módulo',
                                content: 'Haz clic en "Editar Permisos" para abrir el panel de interruptores de cada módulo individual.',
                                placement: 'left',
                                condition: () => !!document.querySelector('button[data-bs-target^="#modalModulo_"]')
                            },
                            {
                                target: '.modal.show .modal-body, .modal[id^="modalModulo_"] .modal-body',
                                title: 'Interruptores de Operaciones',
                                content: 'Activa o desactiva con los interruptores (switches) los accesos específicos que tendrá el rol para este módulo.',
                                placement: 'center',
                                condition: () => !!document.querySelector('button[data-bs-target^="#modalModulo_"]'),
                                action: async () => {
                                    const btn = document.querySelector('button[data-bs-target^="#modalModulo_"]');
                                    if (btn && btn.dataset.bsTarget) {
                                        const modalEl = document.querySelector(btn.dataset.bsTarget);
                                        if (modalEl && typeof bootstrap !== 'undefined') {
                                            bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                            await new Promise(r => setTimeout(r, 300));
                                        }
                                    }
                                },
                                onComplete: () => {
                                    const modalEl = document.querySelector('.modal.show');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: 'button[type="submit"].btn-primary',
                                title: 'Guardar Cambios de Seguridad',
                                content: 'Aplica las modificaciones directamente a la base de datos de seguridad. Los cambios surten efecto de inmediato en las sesiones de los usuarios. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[type="submit"].btn-primary')
                            },
                            {
                                target: null,
                                title: '¡Gestión de Permisos Comprendida!',
                                content: 'Has aprendido cómo funciona la matriz de seguridad y asignación granular de privilegios en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 21. GESTIÓN DE ROLES
            // ==================================================================
            roles: {
                nombre: 'Gestión de Roles',
                icono: 'bi-shield-shaded',
                ruta: '/roles',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Definición de roles organizacionales',
                        icono: 'bi-info-circle',
                        descripcion: 'Padrón de roles, jerarquías y alta de nuevos perfiles.',
                        pasos: [
                            {
                                target: '.card-header',
                                title: 'Padrón de Roles del Concesionario',
                                content: 'Gestiona la jerarquía de perfiles de usuario que definen las responsabilidades y accesos permitidos en AutoMall.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaRoles',
                                title: 'Tabla de Roles Registrados',
                                content: 'Muestra el código (#ID), denominación comercial del rol, descripción de funciones y estado operativo actual.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaRoles tbody tr td .badge',
                                title: 'Estado del Rol',
                                content: 'Indica si el rol está Activo (disponible para asignar a usuarios) o Inactivo (bloqueado operativamente).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaRoles tbody tr td .badge')
                            },
                            {
                                target: 'button[data-bs-target="#modalCrearRol"]',
                                title: 'Registrar Nuevo Rol',
                                content: 'Abre la ventana modal para afiliar una nueva categoría jerárquica en el sistema.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalCrearRol"]')
                            },
                            {
                                target: '.btn-editar-rol',
                                title: 'Modificar Rol',
                                content: 'Permite actualizar el nombre comercial, funciones o estatus del rol en cualquier momento.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-editar-rol')
                            },
                            {
                                target: null,
                                title: '¡Roles Comprendidos!',
                                content: 'Puedes iniciar el recorrido "Cómo registrar un rol" para conocer el formulario de alta.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un rol',
                        icono: 'bi-plus-circle',
                        descripcion: 'Paso a paso en el modal: nombre, descripción de funciones y estatus inicial.',
                        pasos: [
                            {
                                target: 'button[data-bs-target="#modalCrearRol"]',
                                title: 'Acceso al Formulario de Rol',
                                content: 'Presiona este botón para desplegar la ventana modal de alta de rol.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalCrearRol"]')
                            },
                            {
                                target: '#modalCrearRol .modal-content',
                                title: 'Ventana Modal de Nuevo Rol',
                                content: 'Permite formalizar una nueva jerarquía organizativa en el sistema de seguridad.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalCrearRol'),
                                action: async () => {
                                    const modalEl = document.getElementById('modalCrearRol');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#modalCrearRol input[name="nombre_rol"]',
                                title: 'Nombre del Rol (Obligatorio)',
                                content: 'Ingresa la denominación del rol (ej: Supervisor de Taller, Asesor Financiero). Máximo 50 caracteres.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrearRol input[name="nombre_rol"]')
                            },
                            {
                                target: '#modalCrearRol textarea[name="descripcion_rol"]',
                                title: 'Descripción de Responsabilidades',
                                content: 'Detalla las funciones principales y el alcance que tendrán los usuarios con este rol asignado.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrearRol textarea[name="descripcion_rol"]')
                            },
                            {
                                target: '#modalCrearRol select[name="estatus"]',
                                title: 'Estatus Inicial',
                                content: 'Define si el rol se habilita de inmediato (Activo) o permanece en borrador (Inactivo).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrearRol select[name="estatus"]')
                            },
                            {
                                target: '#modalCrearRol button[type="submit"]',
                                title: 'Registrar Rol',
                                content: 'Guarda el rol en la base de datos de seguridad y lo pone a disposición para asignarle permisos. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrearRol button[type="submit"]')
                            },
                            {
                                target: '#modalCrearRol button[data-bs-dismiss="modal"]',
                                title: 'Cancelar',
                                content: 'Cierra el modal y descarta los datos sin realizar modificaciones.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrearRol button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalCrearRol');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Rol Registrado!',
                                content: 'Has conocido cómo registrar nuevos roles jerárquicos en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 22. MÓDULOS Y ACCIONES
            // ==================================================================
            modulos_acciones: {
                nombre: 'Módulos y Acciones',
                icono: 'bi-grid-3x3-gap-fill',
                ruta: '/configuracion',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Catálogo técnico del sistema',
                        icono: 'bi-info-circle',
                        descripcion: 'Registro de módulos de software y acciones estándar admitidas.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Configuración de Sistema',
                                content: 'Catálogo técnico que define los módulos de software integrados y las acciones de seguridad estandarizadas.',
                                placement: 'bottom'
                            },
                            {
                                target: '#configTab',
                                title: 'Pestañas de Navegación',
                                content: 'Permite alternar entre el Catálogo de Módulos (pantallas y controladores) y el Catálogo de Acciones Globales (p_crear, p_leer, etc.).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('configTab')
                            },
                            {
                                target: '#tablaModulos',
                                title: 'Catálogo de Módulos Físicos',
                                content: 'Lista los módulos registrados en el esquema de seguridad con su identificador (#ID) y estatus.',
                                placement: 'top',
                                condition: () => !!document.getElementById('tablaModulos')
                            },
                            {
                                target: 'button[data-bs-target="#modalCrearModulo"]',
                                title: 'Alta de Nuevo Módulo',
                                content: 'Permite registrar un nuevo componente o pantalla en el sistema para habilitar su control por permisos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalCrearModulo"]')
                            },
                            {
                                target: '#acciones-tab',
                                title: 'Pestaña de Acciones Globales',
                                content: 'Haz clic aquí para inspeccionar o crear acciones estándar de control (ej: p_crear, p_leer, p_actualizar, p_eliminar).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('acciones-tab')
                            },
                            {
                                target: '#tablaAcciones',
                                title: 'Matriz de Acciones',
                                content: 'Presenta las acciones registradas en el motor de permisos y su estado activo en el sistema.',
                                placement: 'top',
                                condition: () => !!document.getElementById('tablaAcciones')
                            },
                            {
                                target: null,
                                title: '¡Catálogo Técnico Explicado!',
                                content: 'Has conocido cómo AutoMall estructura sus módulos y acciones de seguridad.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro_modulo: {
                        id: 'registro_modulo',
                        nombre: 'Cómo registrar un módulo técnico',
                        icono: 'bi-plus-circle',
                        descripcion: 'Paso a paso en el modal: nombre del módulo técnico y guardado.',
                        pasos: [
                            {
                                target: 'button[data-bs-target="#modalCrearModulo"]',
                                title: 'Acceso a Nuevo Módulo',
                                content: 'Presiona este botón para abrir la ventana modal de registro técnico de módulo.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalCrearModulo"]')
                            },
                            {
                                target: '#modalCrearModulo .modal-content',
                                title: 'Ventana Modal de Módulo',
                                content: 'Permite dar de alta un nuevo módulo en la arquitectura del sistema.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalCrearModulo'),
                                action: async () => {
                                    const modalEl = document.getElementById('modalCrearModulo');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#modalCrearModulo input[name="nombre_modulo"]',
                                title: 'Nombre del Módulo (Obligatorio)',
                                content: 'Ingresa el nombre técnico de la entidad funcional (ej: Auditoría, Reportes, Catálogo).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('#modalCrearModulo input[name="nombre_modulo"]')
                            },
                            {
                                target: '#modalCrearModulo button[type="submit"]',
                                title: 'Registrar Módulo',
                                content: 'Guarda la entrada en la base de datos para que aparezca disponible en la matriz de permisos. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrearModulo button[type="submit"]')
                            },
                            {
                                target: '#modalCrearModulo button[data-bs-dismiss="modal"]',
                                title: 'Cancelar',
                                content: 'Cierra el modal descartando la operación.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalCrearModulo button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalCrearModulo');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Módulo Registrado!',
                                content: 'Has aprendido cómo registrar módulos de software en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 23. MÉTODOS DE PAGO
            // ==================================================================
            metodos_pago: {
                nombre: 'Métodos de Pago',
                icono: 'bi-wallet2',
                ruta: '/metodos-pago',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Formas de pago admitidas',
                        icono: 'bi-info-circle',
                        descripcion: 'Pago Móvil, Transferencias, Divisas, Zelle y validación de referencias.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Gestión de Métodos de Pago',
                                content: 'Configura las modalidades de pago aceptadas para las ventas de vehículos y servicios mecánicos.',
                                placement: 'bottom'
                            },
                            {
                                target: '.table.table-hover',
                                title: 'Tabla de Métodos de Pago',
                                content: 'Presenta el código identificador (#ID), nombre comercial de la modalidad, requerimiento de referencia y estado.',
                                placement: 'top'
                            },
                            {
                                target: '.table.table-hover tbody tr td:nth-child(3)',
                                title: 'Validación de Referencia Bancaria',
                                content: 'Indica con etiqueta "Sí" si el método exige capturar el número de comprobante bancario para conciliar el pago.',
                                placement: 'top',
                                condition: () => !!document.querySelector('.table.table-hover tbody tr td:nth-child(3)')
                            },
                            {
                                target: 'button[onclick*="abrirModalCrearMetodo"]',
                                title: 'Nuevo Método de Pago',
                                content: 'Abre el formulario modal para habilitar una nueva alternativa de cobro (ej: Zelle, Pago Móvil, Punto de Venta).',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="abrirModalCrearMetodo"]')
                            },
                            {
                                target: '.btn-outline-primary',
                                title: 'Modificar Método',
                                content: 'Permite editar la denominación, si requiere referencia o suspender temporalmente su disponibilidad.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-outline-primary')
                            },
                            {
                                target: null,
                                title: '¡Métodos de Pago Explicados!',
                                content: 'Puedes iniciar el recorrido "Cómo registrar un método" para ver los campos del modal.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un método de pago',
                        icono: 'bi-plus-circle',
                        descripcion: 'Paso a paso en el modal: nombre, requerimiento de referencia y estado.',
                        pasos: [
                            {
                                target: 'button[onclick*="abrirModalCrearMetodo"]',
                                title: 'Acceso al Formulario de Cobro',
                                content: 'Haz clic en este botón para desplegar la ventana modal de registro de método de pago.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="abrirModalCrearMetodo"]')
                            },
                            {
                                target: '#modalMetodo .modal-content',
                                title: 'Ventana Modal de Método de Pago',
                                content: 'Permite incorporar una nueva vía de cobro al catálogo del concesionario.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalMetodo'),
                                action: async () => {
                                    const modalEl = document.getElementById('modalMetodo');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#nombre_metodo',
                                title: 'Nombre del Método (Obligatorio)',
                                content: 'Ingresa la denominación clara (ej: Transferencia Bancaria, Zelle, Efectivo Divisas, Tarjeta de Débito).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre_metodo')
                            },
                            {
                                target: '#requiere_referencia',
                                title: '¿Requiere Número de Referencia?',
                                content: 'Selecciona "Sí" si este método genera comprobante bancario verificable (transferencias, pago móvil), o "No" para pagos en efectivo.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('requiere_referencia')
                            },
                            {
                                target: '#estado',
                                title: 'Estado de la Modalidad',
                                content: 'Determina si el método aparece activo en los selectores de facturación y abonos de clientes.',
                                placement: 'top',
                                condition: () => !!document.getElementById('estado')
                            },
                            {
                                target: '#modalMetodo button[type="submit"]',
                                title: 'Guardar Método',
                                content: 'Registra la modalidad en la base de datos comercial. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalMetodo button[type="submit"]')
                            },
                            {
                                target: '#modalMetodo button[data-bs-dismiss="modal"]',
                                title: 'Cancelar',
                                content: 'Cierra el modal y descarta cualquier cambio sin afectar las finanzas del sistema.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalMetodo button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalMetodo');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Método de Pago Registrado!',
                                content: 'Has aprendido cómo habilitar y parametrizar métodos de pago en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 24. BANCOS
            // ==================================================================
            bancos: {
                nombre: 'Gestión de Bancos',
                icono: 'bi-bank',
                ruta: '/bancos',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Instituciones bancarias aliadas',
                        icono: 'bi-info-circle',
                        descripcion: 'Entidades bancarias oficiales receptoras de transferencias.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Gestión de Bancos',
                                content: 'Catálogo de instituciones financieras receptoras de transferencias y depósitos autorizados.',
                                placement: 'bottom'
                            },
                            {
                                target: '.table.table-hover',
                                title: 'Tabla de Instituciones Bancarias',
                                content: 'Lista las entidades financieras habilitadas con su código de registro, nombre oficial y estado operativo.',
                                placement: 'top'
                            },
                            {
                                target: '.table.table-hover tbody tr td:nth-child(3) .badge',
                                title: 'Estatus del Banco',
                                content: 'Indica si la entidad bancaria está Activa para recibir operaciones de venta o servicio.',
                                placement: 'top',
                                condition: () => !!document.querySelector('.table.table-hover tbody tr td:nth-child(3) .badge')
                            },
                            {
                                target: 'button[onclick*="abrirModalCrear"]',
                                title: 'Nuevo Banco',
                                content: 'Permite afiliar una nueva entidad bancaria al directorio oficial del concesionario.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="abrirModalCrear"]')
                            },
                            {
                                target: '.btn-outline-primary',
                                title: 'Modificar Entidad',
                                content: 'Permite actualizar el nombre de la institución o cambiar su estatus a Inactivo.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.btn-outline-primary')
                            },
                            {
                                target: null,
                                title: '¡Bancos Comprendidos!',
                                content: 'Puedes iniciar el recorrido "Cómo registrar un banco" para conocer los campos del modal.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar un banco aliado',
                        icono: 'bi-plus-circle',
                        descripcion: 'Paso a paso en el modal: nombre de la institución bancaria y estado.',
                        pasos: [
                            {
                                target: 'button[onclick*="abrirModalCrear"]',
                                title: 'Acceso al Alta Bancaria',
                                content: 'Presiona este botón para abrir la ventana modal de registro de nueva entidad bancaria.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="abrirModalCrear"]')
                            },
                            {
                                target: '#modalBanco .modal-content',
                                title: 'Ventana Modal de Banco',
                                content: 'Permite incorporar una nueva institución bancaria aliada al sistema.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalBanco'),
                                action: async () => {
                                    const modalEl = document.getElementById('modalBanco');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#nombre_banco',
                                title: 'Nombre de la Entidad Bancaria (Obligatorio)',
                                content: 'Ingresa la denominación oficial de la institución (ej: Banesco, Banco Mercantil, BBVA Provincial, Banco de Venezuela).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre_banco')
                            },
                            {
                                target: '#modalBanco #estado',
                                title: 'Estado del Registro',
                                content: 'Define si la entidad queda Activa inmediatamente para vincularse a cuentas y cobros.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalBanco #estado')
                            },
                            {
                                target: '#modalBanco button[type="submit"]',
                                title: 'Guardar Banco',
                                content: 'Registra el banco en el catálogo corporativo. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalBanco button[type="submit"]')
                            },
                            {
                                target: '#modalBanco button[data-bs-dismiss="modal"]',
                                title: 'Cancelar',
                                content: 'Cierra el modal descartando los datos sin alterar el catálogo.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalBanco button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalBanco');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Banco Registrado!',
                                content: 'Has aprendido cómo afiliar instituciones bancarias en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 25. MONEDAS
            // ==================================================================
            monedas: {
                nombre: 'Gestión de Monedas',
                icono: 'bi-cash-coin',
                ruta: '/monedas',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Monedas y tasas de cambio',
                        icono: 'bi-info-circle',
                        descripcion: 'Unidades fiduciarias y digitales y tasas operativas.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Gestión de Monedas y Divisas',
                                content: 'Administra las monedas fiduciarias y digitales admitidas para cotizaciones, ventas y pagos.',
                                placement: 'bottom'
                            },
                            {
                                target: '#btnMonedas, #btnDigitales',
                                title: 'Selector de Categoría',
                                content: 'Permite alternar entre el catálogo de Monedas Fiduciarias (Bolívar, Dólar, Euro) y Monedas Digitales (USDT, Bitcoin).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('btnMonedas')
                            },
                            {
                                target: '#seccionMonedas .table',
                                title: 'Tabla de Monedas Registradas',
                                content: 'Muestra identificador, nombre de la moneda, símbolo comercial ($, Bs.) y estado operativo.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#seccionMonedas .table')
                            },
                            {
                                target: 'button[onclick*="abrirModalCrearMoneda"]',
                                title: 'Nuevo Registro Monetario',
                                content: 'Abre la ventana modal para dar de alta una nueva moneda o divisa de curso comercial.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="abrirModalCrearMoneda"]')
                            },
                            {
                                target: '#seccionMonedas .btn-outline-primary',
                                title: 'Editar Moneda',
                                content: 'Permite corregir el símbolo comercial o suspender el estatus de la divisa.',
                                placement: 'left',
                                condition: () => !!document.querySelector('#seccionMonedas .btn-outline-primary')
                            },
                            {
                                target: null,
                                title: '¡Monedas Comprendidas!',
                                content: 'Puedes iniciar el recorrido "Cómo registrar una moneda" para conocer los campos del formulario.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    },
                    registro: {
                        id: 'registro',
                        nombre: 'Cómo registrar una moneda o divisa',
                        icono: 'bi-plus-circle',
                        descripcion: 'Paso a paso en el modal: nombre, símbolo y estado.',
                        pasos: [
                            {
                                target: 'button[onclick*="abrirModalCrearMoneda"]',
                                title: 'Acceso al Registro de Moneda',
                                content: 'Haz clic aquí para abrir el formulario modal de alta de moneda.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="abrirModalCrearMoneda"]')
                            },
                            {
                                target: '#modalMoneda .modal-content',
                                title: 'Ventana Modal de Moneda',
                                content: 'Permite incorporar una nueva unidad monetaria al sistema multimoneda de AutoMall.',
                                placement: 'center',
                                condition: () => !!document.getElementById('modalMoneda'),
                                action: async () => {
                                    const modalEl = document.getElementById('modalMoneda');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getOrCreateInstance(modalEl).show();
                                        await new Promise(r => setTimeout(r, 300));
                                    }
                                }
                            },
                            {
                                target: '#nombre_registro',
                                title: 'Nombre de la Moneda (Obligatorio)',
                                content: 'Ingresa la denominación oficial (ej: Dólar Estadounidense, Bolívar Digital, Euro, Tether USDT).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('nombre_registro')
                            },
                            {
                                target: '#simbolo_registro',
                                title: 'Símbolo Monetario',
                                content: 'Signo o abreviatura gráfica que precederá los montos (ej: $, Bs., €, USDT).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('simbolo_registro')
                            },
                            {
                                target: '#estado_registro',
                                title: 'Estado del Registro',
                                content: 'Determina si la moneda está Activa para cotizaciones y cobros en el sistema.',
                                placement: 'top',
                                condition: () => !!document.getElementById('estado_registro')
                            },
                            {
                                target: '#modalMoneda button[type="submit"]',
                                title: 'Guardar Moneda',
                                content: 'Guarda la divisa en la base de datos de configuración. (No se enviará durante la visita).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalMoneda button[type="submit"]')
                            },
                            {
                                target: '#modalMoneda button[data-bs-dismiss="modal"]',
                                title: 'Cancelar',
                                content: 'Cierra el modal y descarta los datos sin alterar las unidades monetarias.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#modalMoneda button[data-bs-dismiss="modal"]'),
                                onComplete: () => {
                                    const modalEl = document.getElementById('modalMoneda');
                                    if (modalEl && typeof bootstrap !== 'undefined') {
                                        bootstrap.Modal.getInstance(modalEl)?.hide();
                                    }
                                }
                            },
                            {
                                target: null,
                                title: '¡Moneda Registrada!',
                                content: 'Has aprendido cómo parametrizar y registrar monedas en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Guía'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 26. BITÁCORA DEL SISTEMA
            // ==================================================================
            bitacora: {
                nombre: 'Bitácora del Sistema',
                icono: 'bi-list-check',
                ruta: '/bitacora',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Auditoría cronológica de eventos',
                        icono: 'bi-info-circle',
                        descripcion: 'Trazabilidad de seguridad, inicios de sesión y modificaciones críticas.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Bitácora del Sistema',
                                content: 'Registro inmutable de auditoría forense que documenta de manera cronológica cada interacción y evento en AutoMall.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaBitacora',
                                title: 'Tabla de Auditoría',
                                content: 'Centraliza los eventos con fecha, hora exacta, usuario responsable, rol, módulo intervenido y detalle de la acción ejecutada.',
                                placement: 'top'
                            },
                            {
                                target: '#tablaBitacora thead th:nth-child(1)',
                                title: 'Fecha y Hora',
                                content: 'Estampa cronológica precisa con formato dd/mm/aaaa hh:mm:ss generada por el servidor al momento del suceso.',
                                placement: 'bottom'
                            },
                            {
                                target: '#tablaBitacora tbody tr td:nth-child(2)',
                                title: 'Identificación del Usuario',
                                content: 'Muestra la cédula de identidad y nombres completos del operador que ejecutó la acción auditada.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaBitacora tbody tr td:nth-child(2)')
                            },
                            {
                                target: '#tablaBitacora tbody tr td:nth-child(4) .badge',
                                title: 'Módulo Intervenido',
                                content: 'Etiqueta identificativa de la pantalla o controlador afectado (ej: Ventas, Vehículos, Usuarios, Citas).',
                                placement: 'top',
                                condition: () => !!document.querySelector('#tablaBitacora tbody tr td:nth-child(4) .badge')
                            },
                            {
                                target: '.dataTables_filter input',
                                title: 'Búsqueda Rápida de Auditoría',
                                content: 'Permite filtrar instantáneamente por cédula, módulo, fecha o tipo de acción en todo el historial auditado.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('.dataTables_filter input')
                            },
                            {
                                target: 'button[onclick*="window.print"]',
                                title: 'Imprimir Reporte Oficial',
                                content: 'Genera una copia impresa o archivo PDF oficial para revisiones de control interno o auditorías externas.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="window.print"]')
                            },
                            {
                                target: null,
                                title: '¡Auditoría y Bitácora Explicada!',
                                content: 'Has aprendido cómo AutoMall garantiza la transparencia, trazabilidad y seguridad de la información.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 27. MANTENIMIENTO A LA BD
            // ==================================================================
            mantenimiento_bd: {
                nombre: 'Mantenimiento de BD',
                icono: 'bi-database-fill-gear',
                ruta: '/mantenimiento',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Respaldos y restauración controlada',
                        icono: 'bi-info-circle',
                        descripcion: 'Exportación de archivos .sql descargables y utilidades de restauración.',
                        pasos: [
                            {
                                target: 'h2',
                                title: 'Mantenimiento del Sistema y Bases de Datos',
                                content: 'Consola de respaldo y restauración para resguardar la continuidad operativa de AutoMall y su esquema de seguridad.',
                                placement: 'bottom'
                            },
                            {
                                target: '.card:has(button[onclick*="automall"]), .col-md-6:first-child .card',
                                title: 'Módulo de Base de Datos: Automall',
                                content: 'Contiene toda la información comercial y operativa del concesionario: vehículos, clientes, ventas, mantenimientos y servicios.',
                                placement: 'top'
                            },
                            {
                                target: 'button[onclick*="automall"]',
                                title: 'Exportar Respaldo de Negocio',
                                content: 'Genera y descarga en tu computadora un archivo .sql con la estructura y datos íntegros de la base automall.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="automall"]')
                            },
                            {
                                target: '#file-automall',
                                title: 'Importación y Restauración de Negocio',
                                content: 'Permite seleccionar un archivo .sql descargado previamente para restaurar el estado de los datos ante contingencias.',
                                placement: 'top',
                                condition: () => !!document.getElementById('file-automall')
                            },
                            {
                                target: '.card:has(button[onclick*="seguridad"]), .col-md-6:last-child .card',
                                title: 'Módulo de Base de Datos: Seguridad',
                                content: 'Almacena las cuentas de usuario, roles jerárquicos, matriz granular de permisos y la bitácora histórica de auditoría.',
                                placement: 'top'
                            },
                            {
                                target: 'button[onclick*="seguridad"]',
                                title: 'Exportar Respaldo de Seguridad',
                                content: 'Descarga un archivo .sql con la copia de resguardo del esquema de autenticación y accesos.',
                                placement: 'bottom',
                                condition: () => !!document.querySelector('button[onclick*="seguridad"]')
                            },
                            {
                                target: '#file-seguridad',
                                title: 'Restauración de Seguridad',
                                content: 'Permite recuperar la configuración de cuentas y permisos mediante la carga de un respaldo .sql válido.',
                                placement: 'top',
                                condition: () => !!document.getElementById('file-seguridad')
                            },
                            {
                                target: null,
                                title: '¡Mantenimiento de BD Comprendido!',
                                content: 'Recuerda generar respaldos periódicos antes de realizar actualizaciones estructurales o mantenimiento masivo.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 28. REPORTES ESTADÍSTICOS
            // ==================================================================
            estadisticas: {
                nombre: 'Reportes Estadísticos',
                icono: 'bi-file-earmark-bar-graph-fill',
                ruta: '/reportes/estadisticas',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Panel gerencial y analítica gráfica',
                        icono: 'bi-info-circle',
                        descripcion: 'Métricas clave (KPIs), comparativas y exportación en PDF/Excel.',
                        pasos: [
                            {
                                target: '#titulo-reporte',
                                title: 'Panel de Estadísticas Gerenciales',
                                content: 'Módulo de Business Intelligence (BI) para visualizar indicadores clave de rendimiento (KPIs) y gráficos interactivos.',
                                placement: 'bottom'
                            },
                            {
                                target: '#selector-reporte',
                                title: 'Selector de Módulo a Analizar',
                                content: 'Permite elegir el área operativa a consultar: Ventas, Vehículos, Mantenimiento, Servicios, Citas, Compras e Insumos o Pagos.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('selector-reporte')
                            },
                            {
                                target: '#btn-generar',
                                title: 'Botón Generar',
                                content: 'Procesa la información en tiempo real, calcula las métricas y dibuja los gráficos interactivos mediante ApexCharts.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('btn-generar')
                            },
                            {
                                target: '.dropdown button.btn-success',
                                title: 'Exportar Informes',
                                content: 'Despliega las opciones de exportación consolidada para descargar el informe en formato PDF o documento Excel.',
                                placement: 'left',
                                condition: () => !!document.querySelector('.dropdown button.btn-success')
                            },
                            {
                                target: '#filtros-container, .card:has(#filtros-container)',
                                title: 'Filtros Dinámicos del Módulo',
                                content: 'Al seleccionar un módulo, este panel despliega filtros especializados (rangos de fechas, clientes, talleres, estatus).',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('filtros-container')
                            },
                            {
                                target: '#kpi-container',
                                title: 'Tarjetas de Indicadores Clave (KPIs)',
                                content: 'Presenta totales monetarios, promedios de atención, cantidades de unidades operadas y tasas de conversión en tarjetas resumidas.',
                                placement: 'top',
                                condition: () => !!document.getElementById('kpi-container')
                            },
                            {
                                target: '#charts-container',
                                title: 'Gráficos Estadísticos Interactivos',
                                content: 'Renderiza gráficos de barras, líneas temporales y diagramas circulares para análisis comparativo y tendencias.',
                                placement: 'top',
                                condition: () => !!document.getElementById('charts-container')
                            },
                            {
                                target: null,
                                title: '¡Panel Gerencial Explicado!',
                                content: 'Has aprendido cómo extraer valor estratégico de los reportes y estadísticas de AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            },

            // ==================================================================
            // 29. MI PERFIL
            // ==================================================================
            perfil: {
                nombre: 'Mi Perfil',
                icono: 'bi-person-circle',
                ruta: '/perfil',
                disponible: true,
                subtours: {
                    general: {
                        id: 'general',
                        nombre: 'Mi cuenta personal y seguridad',
                        icono: 'bi-info-circle',
                        descripcion: 'Ficha de usuario, foto de perfil, datos de contacto y cambio de contraseña.',
                        pasos: [
                            {
                                target: '.card-profile-sidebar',
                                title: 'Ficha del Usuario Autenticado',
                                content: 'Muestra tu fotografía de perfil, nombre completo, rol asignado, correo institucional y dirección registrada.',
                                placement: 'bottom'
                            },
                            {
                                target: '#profileTabs',
                                title: 'Pestañas de Configuración de Cuenta',
                                content: 'Permite alternar entre la consulta de Datos Personales y la sección de Seguridad de Acceso.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('profileTabs')
                            },
                            {
                                target: '#datos-panel .profile-data-box',
                                title: 'Datos Personales Registrados',
                                content: 'Detalla tu cédula de identidad, teléfono de contacto y dirección residencial registrada en el sistema.',
                                placement: 'top',
                                condition: () => !!document.querySelector('#datos-panel .profile-data-box')
                            },
                            {
                                target: 'button[data-bs-target="#modalDatos"]',
                                title: 'Editar Perfil y Fotografía',
                                content: 'Abre el modal para actualizar tu número telefónico, dirección física y cargar una nueva imagen de perfil.',
                                placement: 'top',
                                condition: () => !!document.querySelector('button[data-bs-target="#modalDatos"]')
                            },
                            {
                                target: '#password-tab',
                                title: 'Pestaña de Seguridad de Acceso',
                                content: 'Haz clic aquí para gestionar tus credenciales y preguntas secretas de recuperación.',
                                placement: 'bottom',
                                condition: () => !!document.getElementById('password-tab')
                            },
                            {
                                target: 'form[action*="cambiar_password_perfil"]',
                                title: 'Renovación Segura de Contraseña',
                                content: 'Formulario protegido para actualizar tu clave: exige validar tu contraseña actual antes de registrar la nueva clave.',
                                placement: 'top',
                                condition: () => !!document.querySelector('form[action*="cambiar_password_perfil"]')
                            },
                            {
                                target: 'form[action*="guardar_preguntas"], form[action*="actualizar_preguntas"]',
                                title: 'Preguntas de Seguridad',
                                content: 'Permite afiliar o renovar preguntas secretas para recuperar el acceso a tu cuenta de manera autónoma en caso de olvido.',
                                placement: 'top',
                                condition: () => !!document.querySelector('form[action*="guardar_preguntas"], form[action*="actualizar_preguntas"]')
                            },
                            {
                                target: null,
                                title: '¡Perfil Comprendido!',
                                content: 'Has aprendido cómo mantener al día tu ficha personal y tus credenciales de seguridad en AutoMall.',
                                placement: 'center',
                                finishLabel: 'Finalizar Recorrido'
                            }
                        ]
                    }
                }
            }
        };
    }

    /**
     * Retorna la definición de un módulo
     * @param {string} moduleKey
     * @returns {Object|null}
     */
    static getModule(moduleKey) {
        const catalog = this.getModuleDefinitions();
        return catalog[moduleKey] || null;
    }

    /**
     * Indica si un módulo o subtour específico está disponible
     * @param {string} moduleKey
     * @param {string} subtourId
     * @returns {boolean}
     */
    static isAvailable(moduleKey, subtourId = 'general') {
        const mod = this.getModule(moduleKey);
        if (!mod || !mod.disponible) return false;

        // Si tiene subtours estructurados
        if (mod.subtours && mod.subtours[subtourId]) {
            const subtour = mod.subtours[subtourId];
            return Array.isArray(subtour.pasos) && subtour.pasos.length > 0;
        }

        // Si tuviera array de pasos directos
        if (Array.isArray(mod.pasos) && mod.pasos.length > 0) {
            return true;
        }

        return false;
    }

    /**
     * Obtiene los pasos filtrados por condiciones activas de permisos y DOM
     * @param {string} moduleKey
     * @param {string} subtourId
     * @returns {Array<Object>}
     */
    static getSteps(moduleKey, subtourId = 'general') {
        const mod = this.getModule(moduleKey);
        if (!mod) return [];

        let pasosRaw = [];
        if (mod.subtours && mod.subtours[subtourId]) {
            pasosRaw = mod.subtours[subtourId].pasos || [];
        } else if (Array.isArray(mod.pasos)) {
            pasosRaw = mod.pasos;
        }

        // Filtra los pasos según la condición de existencia en DOM (permiso real del usuario)
        return pasosRaw.filter(step => {
            if (typeof step.condition === 'function') {
                try {
                    return step.condition();
                } catch (e) {
                    console.warn('[AutoMall TourSteps] Error evaluando condición de paso:', e);
                    return false;
                }
            }
            return true;
        });
    }

    /**
     * Obtiene el nombre amigable de un subtour
     */
    static getSubtourTitle(moduleKey, subtourId = 'general') {
        const mod = this.getModule(moduleKey);
        if (mod && mod.subtours && mod.subtours[subtourId]) {
            return `${mod.nombre}: ${mod.subtours[subtourId].nombre}`;
        }
        return mod ? mod.nombre : 'Guía';
    }
}
