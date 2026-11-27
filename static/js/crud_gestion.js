/**
 * =========================================================
 * UTILIDADES GENERALES Y VALIDACIONES
 * =========================================================
 */

// Instanciador seguro de Modales
function getModalInstance(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return null;
    return bootstrap.Modal.getOrCreateInstance(modalElement);
}

// Validador de texto vacío
function esTextoValido(texto) {
    return texto !== null && texto !== undefined && texto.trim() !== '';
}

// Disparador de Alertas de Error
function mostrarAlertaError(mensaje) {
    Swal.fire({
        icon: 'warning',
        title: 'Validación',
        text: mensaje,
        confirmButtonColor: '#0d6efd'
    });
}

/**
 * =========================================================
 * MÓDULO: MÉTODOS DE PAGO
 * =========================================================
 */

function abrirModalCrearMetodo() {
    document.getElementById('formMetodo').reset();
    document.getElementById('modalTitulo').innerText = 'Nuevo Método de Pago';
    document.getElementById('url_destino').value = '/metodos-pago/gestion';
    
    getModalInstance('modalMetodo').show();
}

function abrirModalEditarMetodo(id, nombre, requiere_ref, estado) {
    document.getElementById('nombre_metodo').value = nombre;
    // Manejar booleanos o enteros
    document.getElementById('requiere_referencia').value = (requiere_ref === '1' || requiere_ref === 'True' || requiere_ref === true) ? '1' : '0';
    document.getElementById('estado').value = estado;
    
    document.getElementById('modalTitulo').innerText = 'Editar Método';
    document.getElementById('url_destino').value = '/metodos-pago/editar/' + id;
    
    getModalInstance('modalMetodo').show();
}

async function guardarMetodo(e) {
    e.preventDefault();
    
    // 1. Validaciones Frontend
    const nombreMetodo = document.getElementById('nombre_metodo').value;
    
    if (!esTextoValido(nombreMetodo)) {
        mostrarAlertaError('El nombre del método de pago no puede estar vacío.');
        return;
    }
    if (nombreMetodo.trim().length < 3) {
        mostrarAlertaError('El nombre del método debe tener al menos 3 caracteres.');
        return;
    }

    // 2. Preparar envío
    const url = document.getElementById('url_destino').value;
    const formData = new FormData(document.getElementById('formMetodo'));

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.status === 'success') {
            getModalInstance('modalMetodo').hide();
            Swal.fire('¡Éxito!', data.message, 'success').then(() => location.reload());
        } else {
            Swal.fire('Error', data.message || 'Ocurrió un error en el servidor', 'error');
        }
    } catch (error) {
        console.error(error);
        Swal.fire('Error', 'Ocurrió un problema de comunicación con el servidor.', 'error');
    }
}

function eliminarMetodo(id) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "El método de pago será desactivado/eliminado.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, proceder',
        cancelButtonText: 'Cancelar'
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                const response = await fetch('/metodos-pago/eliminar/' + id, { method: 'POST' });
                const data = await response.json();
                
                if (data.status === 'success') {
                    Swal.fire('¡Realizado!', data.message, 'success').then(() => location.reload());
                } else {
                    Swal.fire('Error', data.message, 'error');
                }
            } catch (error) {
                Swal.fire('Error', 'Ocurrió un problema de red.', 'error');
            }
        }
    });
}


/**
 * =========================================================
 * MÓDULO: MONEDAS Y MONEDAS DIGITALES
 * =========================================================
 */

let tipoActual = 'moneda';

function mostrarSeccion(tipo) {
    const monedas = document.getElementById('seccionMonedas');
    const digitales = document.getElementById('seccionDigitales');
    const btnMonedas = document.getElementById('btnMonedas');
    const btnDigitales = document.getElementById('btnDigitales');

    tipoActual = tipo;

    if (tipo === 'monedas') {
        monedas.style.display = 'block';
        digitales.style.display = 'none';
        btnMonedas.className = 'btn btn-primary';
        btnDigitales.className = 'btn btn-outline-primary';
    } else {
        monedas.style.display = 'none';
        digitales.style.display = 'block';
        btnDigitales.className = 'btn btn-primary';
        btnMonedas.className = 'btn btn-outline-primary';
    }
}

function abrirModalCrearMoneda() {
    const form = document.getElementById('formMoneda');
    const nombreInput = document.getElementById('nombre_registro');
    const simboloInput = document.getElementById('simbolo_registro');
    const estadoInput = document.getElementById('estado_registro');

    form.reset();

    if (tipoActual === 'digitales') {
        document.getElementById('tipo_registro').value = 'digital';
        document.getElementById('modalTitulo').innerText = 'Nueva Moneda Digital';
        document.getElementById('url_destino').value = '/monedas-digitales/crear';

        nombreInput.name = 'nombre_digital';
        simboloInput.name = 'simbolo_digital';
        estadoInput.name = 'estado_digital';

        estadoInput.innerHTML = `
            <option value="1">Activo</option>
            <option value="0">Inactivo</option>
        `;
        estadoInput.value = '1';
    } else {
        document.getElementById('tipo_registro').value = 'moneda';
        document.getElementById('modalTitulo').innerText = 'Nueva Moneda';
        document.getElementById('url_destino').value = '/monedas/crear';

        nombreInput.name = 'nombre_moneda';
        simboloInput.name = 'simbolo';
        estadoInput.name = 'estado';

        estadoInput.innerHTML = `
            <option value="Activo">Activo</option>
            <option value="Inactivo">Inactivo</option>
        `;
        estadoInput.value = 'Activo';
    }

    getModalInstance('modalMoneda').show();
}

function abrirModalEditarMoneda(id, nombre, simbolo, estado) {
    tipoActual = 'monedas';
    document.getElementById('tipo_registro').value = 'moneda';
    document.getElementById('modalTitulo').innerText = 'Editar Moneda';
    document.getElementById('url_destino').value = '/monedas/editar/' + id;

    const nombreInput = document.getElementById('nombre_registro');
    nombreInput.name = 'nombre_moneda';
    nombreInput.value = nombre;

    const simboloInput = document.getElementById('simbolo_registro');
    simboloInput.name = 'simbolo';
    simboloInput.value = simbolo;

    const estadoInput = document.getElementById('estado_registro');
    estadoInput.name = 'estado';
    estadoInput.innerHTML = `
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
    `;
    estadoInput.value = estado;

    getModalInstance('modalMoneda').show();
}

// Se agrega la función faltante para editar monedas digitales
function abrirModalEditarDigital(id, nombre, simbolo, estado) {
    tipoActual = 'digitales';
    document.getElementById('tipo_registro').value = 'digital';
    document.getElementById('modalTitulo').innerText = 'Editar Moneda Digital';
    document.getElementById('url_destino').value = '/monedas-digitales/editar/' + id;

    const nombreInput = document.getElementById('nombre_registro');
    nombreInput.name = 'nombre_digital';
    nombreInput.value = nombre;

    const simboloInput = document.getElementById('simbolo_registro');
    simboloInput.name = 'simbolo_digital';
    simboloInput.value = simbolo;

    const estadoInput = document.getElementById('estado_registro');
    estadoInput.name = 'estado_digital';
    estadoInput.innerHTML = `
        <option value="1">Activo</option>
        <option value="0">Inactivo</option>
    `;
    // Mapeo seguro para el estado si viene como True/False, 1/0 o Activo/Inactivo
    estadoInput.value = (estado === '1' || estado === 'True' || estado === true || estado === 'Activo') ? '1' : '0';

    getModalInstance('modalMoneda').show();
}

// Se completa la función guardarRegistro
async function guardarRegistro(e) {
    e.preventDefault();

    // 1. Validaciones Frontend
    const nombreRegistro = document.getElementById('nombre_registro').value;
    const simboloRegistro = document.getElementById('simbolo_registro').value;

    if (!esTextoValido(nombreRegistro)) {
        mostrarAlertaError('El nombre de la moneda es obligatorio.');
        return;
    }
    
    // Opcional: Validar longitud máxima/mínima del símbolo si lo deseas
    if (simboloRegistro.trim().length > 10) {
        mostrarAlertaError('El símbolo es demasiado largo.');
        return;
    }

    // 2. Preparar envío
    const url = document.getElementById('url_destino').value;
    const formData = new FormData(document.getElementById('formMoneda'));

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.status === 'success') {
            getModalInstance('modalMoneda').hide();
            Swal.fire('¡Éxito!', data.message, 'success').then(() => location.reload());
        } else {
            Swal.fire('Error', data.message || 'Error al guardar.', 'error');
        }
    } catch (error) {
        console.error(error);
        Swal.fire('Error', 'Problema de red al intentar guardar.', 'error');
    }
}

// Se completa la función eliminar (para físicas)
function eliminarMoneda(id) {
    confirmarEliminacion('/monedas/eliminar/' + id, 'La moneda será eliminada/desactivada.');
}

// Se completa la función eliminar (para digitales)
function eliminarMonedaDigital(id) {
    confirmarEliminacion('/monedas-digitales/eliminar/' + id, 'La moneda digital será eliminada/desactivada.');
}

// Función auxiliar para no repetir código en SweetAlert de eliminación
function confirmarEliminacion(url, mensaje) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: mensaje,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, proceder',
        cancelButtonText: 'Cancelar'
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                const response = await fetch(url, { method: 'POST' });
                const data = await response.json();
                
                if (data.status === 'success') {
                    Swal.fire('¡Realizado!', data.message, 'success').then(() => location.reload());
                } else {
                    Swal.fire('Error', data.message, 'error');
                }
            } catch (error) {
                Swal.fire('Error', 'Ocurrió un problema de red.', 'error');
            }
        }
    });
}