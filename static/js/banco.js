(function () {
    'use strict';

    // ============================================
    // Función auxiliar para instanciar el modal de forma segura con Bootstrap 5
    // ============================================
    function getModalInstance() {
        const modalElement = document.getElementById('modalBanco');
        return bootstrap.Modal.getOrCreateInstance(modalElement);
    }

    function abrirModalCrear() {
        document.getElementById('formBanco').reset();
        document.getElementById('modalTitulo').innerText = 'Nuevo Banco';
        document.getElementById('url_destino').value = '/bancos/gestion'; // POST para registrar

        getModalInstance().show();
    }

    function abrirModalEditar(id, nombre, estado) {
        document.getElementById('nombre_banco').value = nombre;
        document.getElementById('estado').value = estado;

        document.getElementById('modalTitulo').innerText = 'Editar Banco';
        document.getElementById('url_destino').value = '/bancos/editar/' + id; // POST para actualizar

        getModalInstance().show();
    }

    async function guardarBanco(e) {
        e.preventDefault();
        const url = document.getElementById('url_destino').value;
        const formData = new FormData(document.getElementById('formBanco'));

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.status === 'success') {
                getModalInstance().hide();
                Swal.fire('¡Éxito!', data.message, 'success').then(() => location.reload());
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        } catch (error) {
            Swal.fire('Error', 'Ocurrió un problema de red.', 'error');
        }
    }

    function eliminarBanco(id) {
        Swal.fire({
            title: '¿Estás seguro?',
            text: "El banco será marcado como Inactivo.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, desactivar',
            cancelButtonText: 'Cancelar'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const response = await fetch('/bancos/eliminar/' + id, { method: 'POST' });
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
    window.abrirModalCrear  = abrirModalCrear;
    window.abrirModalEditar = abrirModalEditar;
    window.guardarBanco     = guardarBanco;
    window.eliminarBanco    = eliminarBanco;
})();