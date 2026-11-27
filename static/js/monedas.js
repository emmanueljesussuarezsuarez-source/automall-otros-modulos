(function () {
    'use strict';

    let tipoActual = 'moneda';

    // =========================================================
    // MODAL
    // =========================================================
    function getModalInstance() {
        const modalElement = document.getElementById('modalMoneda');
        return bootstrap.Modal.getOrCreateInstance(modalElement);
    }

    // =========================================================
    // CAMBIAR ENTRE MONEDAS Y DIGITALES
    // =========================================================
    function mostrarSeccion(tipo) {
        const monedas     = document.getElementById('seccionMonedas');
        const digitales   = document.getElementById('seccionDigitales');
        const btnMonedas  = document.getElementById('btnMonedas');
        const btnDigitales = document.getElementById('btnDigitales');

        tipoActual = tipo;

        if (tipo === 'monedas') {
            monedas.style.display = 'block';
            digitales.style.display = 'none';

            btnMonedas.classList.remove('btn-outline-primary');
            btnMonedas.classList.add('btn-primary');

            btnDigitales.classList.remove('btn-primary');
            btnDigitales.classList.add('btn-outline-primary');
        } else {
            monedas.style.display = 'none';
            digitales.style.display = 'block';

            btnDigitales.classList.remove('btn-outline-primary');
            btnDigitales.classList.add('btn-primary');

            btnMonedas.classList.remove('btn-primary');
            btnMonedas.classList.add('btn-outline-primary');
        }
    }

    // =========================================================
    // CREAR MONEDA
    // =========================================================
    function abrirModalCrear() {
        const form         = document.getElementById('formMoneda');
        const nombreInput  = document.getElementById('nombre_registro');
        const simboloInput = document.getElementById('simbolo_registro');
        const estadoInput  = document.getElementById('estado_registro');

        form.reset();

        if (tipoActual === 'digitales') {
            // =========================================
            // NUEVA MONEDA DIGITAL
            // =========================================
            document.getElementById('tipo_registro').value = 'digital';
            document.getElementById('modalTitulo').innerText = 'Nueva Moneda Digital';
            document.getElementById('url_destino').value = '/monedas-digitales/crear';

            nombreInput.name = 'nombre_digital';
            nombreInput.value = '';

            simboloInput.name = 'simbolo_digital';
            simboloInput.value = '';

            estadoInput.name = 'estado_digital';
            estadoInput.innerHTML = `
                <option value="1">Activo</option>
                <option value="0">Inactivo</option>
            `;
            estadoInput.value = '1';
        } else {
            // =========================================
            // NUEVA MONEDA
            // =========================================
            document.getElementById('tipo_registro').value = 'moneda';
            document.getElementById('modalTitulo').innerText = 'Nueva Moneda';
            document.getElementById('url_destino').value = '/monedas/crear';

            nombreInput.name = 'nombre_moneda';
            nombreInput.value = '';

            simboloInput.name = 'simbolo';
            simboloInput.value = '';

            estadoInput.name = 'estado';
            estadoInput.innerHTML = `
                <option value="Activo">Activo</option>
                <option value="Inactivo">Inactivo</option>
            `;
            estadoInput.value = 'Activo';
        }

        getModalInstance().show();
    }

    // =========================================================
    // EDITAR MONEDA
    // =========================================================
    function abrirModalEditarMoneda(id, nombre, simbolo, estado) {
        tipoActual = 'moneda';
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

        getModalInstance().show();
    }

    // =========================================================
    // EDITAR MONEDA DIGITAL
    // =========================================================
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
        estadoInput.value = (estado == '1' || estado == 'True') ? '1' : '0';

        getModalInstance().show();
    }

    // =========================================================
    // GUARDAR
    // =========================================================
    async function guardarRegistro(e) {
        e.preventDefault();

        const url = document.getElementById('url_destino').value;
        const form = document.getElementById('formMoneda');
        const formData = new FormData(form);

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.status === 'success') {
                getModalInstance().hide();
                Swal.fire('¡Éxito!', data.message, 'success').then(() => {
                    location.reload();
                });
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        } catch (error) {
            Swal.fire('Error', 'Ocurrió un problema de red.', 'error');
        }
    }

    // =========================================================
    // ELIMINAR MONEDA
    // =========================================================
    function eliminarMoneda(id) {
        Swal.fire({
            title: '¿Estás seguro?',
            text: 'La moneda será marcada como Inactiva.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, desactivar',
            cancelButtonText: 'Cancelar'
        }).then(async (result) => {
            if (!result.isConfirmed) return;

            try {
                const response = await fetch('/monedas/eliminar/' + id, {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.status === 'success') {
                    Swal.fire('¡Desactivada!', data.message, 'success').then(() => {
                        location.reload();
                    });
                } else {
                    Swal.fire('Error', data.message, 'error');
                }
            } catch (error) {
                Swal.fire('Error', 'Ocurrió un problema de red.', 'error');
            }
        });
    }

    // =========================================================
    // ELIMINAR MONEDA DIGITAL
    // =========================================================
    function eliminarMonedaDigital(id) {
        Swal.fire({
            title: '¿Estás seguro?',
            text: 'La moneda digital será marcada como Inactiva.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, desactivar',
            cancelButtonText: 'Cancelar'
        }).then(async (result) => {
            if (!result.isConfirmed) return;

            try {
                const response = await fetch('/monedas-digitales/eliminar/' + id, {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.status === 'success') {
                    Swal.fire('¡Desactivada!', data.message, 'success').then(() => {
                        location.reload();
                    });
                } else {
                    Swal.fire('Error', data.message, 'error');
                }
            } catch (error) {
                Swal.fire('Error', 'Ocurrió un problema de red.', 'error');
            }
        });
    }

    // =========================================================
    // Exponer funciones usadas en atributos onclick del HTML
    // =========================================================
    window.abrirModalCrearMoneda  = abrirModalCrear;
    window.mostrarSeccion         = mostrarSeccion;
    window.abrirModalEditarMoneda = abrirModalEditarMoneda;
    window.abrirModalEditarDigital = abrirModalEditarDigital;
    window.guardarRegistro        = guardarRegistro;
    window.eliminarMoneda         = eliminarMoneda;
    window.eliminarMonedaDigital  = eliminarMonedaDigital;
})();