(function () {
    'use strict';

    // ============================================
    // Función auxiliar para instanciar el modal de forma segura (sin errores de carga previa)
    // ============================================
    function getModalInstance() {
        const modalElement = document.getElementById('modalMetodo');
        return bootstrap.Modal.getOrCreateInstance(modalElement);
    }

    function abrirModalCrear() {
        document.getElementById('formMetodo').reset();
        document.getElementById('modalTitulo').innerText = 'Nuevo Método de Pago';
        document.getElementById('url_destino').value = '/metodos-pago/gestion'; // POST a la ruta general

        getModalInstance().show(); // <-- Abrimos el modal de forma segura
    }

    function abrirModalEditar(id, nombre, requiere_ref, estado) {
        document.getElementById('nombre_metodo').value = nombre;
        // Manejar el valor booleano o entero que llegue de la base de datos
        document.getElementById('requiere_referencia').value = (requiere_ref == '1' || requiere_ref == 'True') ? '1' : '0';
        document.getElementById('estado').value = estado;

        document.getElementById('modalTitulo').innerText = 'Editar Método';
        document.getElementById('url_destino').value = '/metodos-pago/editar/' + id;

        getModalInstance().show(); // <-- Abrimos el modal de forma segura
    }

    async function guardarMetodo(e) {
        e.preventDefault();
        const url = document.getElementById('url_destino').value;
        const formData = new FormData(document.getElementById('formMetodo'));

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.status === 'success') {
                getModalInstance().hide(); // <-- Ocultamos de forma segura
                Swal.fire('¡Éxito!', data.message, 'success').then(() => location.reload());
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        } catch (error) {
            Swal.fire('Error', 'Ocurrió un problema de red.', 'error');
        }
    }

    function eliminarMetodo(id) {
        Swal.fire({
            title: '¿Estás seguro?',
            text: "El método de pago será desactivado.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, desactivar',
            cancelButtonText: 'Cancelar'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const response = await fetch('/metodos-pago/eliminar/' + id, { method: 'POST' });
                    const data = await response.json();

                    if (data.status === 'success') {
                        Swal.fire('¡Desactivado!', data.message, 'success').then(() => location.reload());
                    } else {
                        Swal.fire('Error', data.message, 'error');
                    }
                } catch (error) {
                    Swal.fire('Error', 'Ocurrió un problema de red.', 'error');
                }
            }
        });
    }

    // ============================================
    // Exponer funciones usadas en atributos onclick del HTML
    // ============================================
    window.abrirModalCrearMetodo = abrirModalCrear;
    window.abrirModalEditar      = abrirModalEditar;
    window.guardarMetodo         = guardarMetodo;
    window.eliminarMetodo        = eliminarMetodo;
})();