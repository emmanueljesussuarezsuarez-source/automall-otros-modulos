document.addEventListener('DOMContentLoaded', function(){
    'use strict';

    // 1. MENSAJES FLASH AUTO-SWEETALERT2
    const msgElements = document.querySelectorAll('.flask-msg-data');
    msgElements.forEach(el => {
        const mensaje = el.dataset.message;
        const categoria = el.dataset.category; 

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: categoria === 'success' ? '¡Éxito!' : (categoria === 'warning' ? 'Advertencia' : 'Aviso'),
                text: mensaje,
                icon: categoria === 'error' ? 'error' : (categoria === 'success' ? 'success' : 'info'),
                timer: 4000,
                timerProgressBar: true,
                confirmButtonColor: '#3085d6'
            });
        }
    });

    // 2. FLATPICKR INICIALIZACIÓN
    const fpHora = flatpickr("#hora_cita", {
        locale: "es",
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i:S",
        time_24hr: true,
        minuteIncrement: 30,
        minTime: "8:00",
        maxTime: "18:00",
        allowInput: false,
        onOpen: function(selectedDates, dateStr, instance) {
            if (instance.timeContainer) {
                const inputs = instance.timeContainer.querySelectorAll('input');
                inputs.forEach(input => {
                    input.addEventListener('input', function() {
                        this.value = this.value.replace(/\D/g, '');
                    });
                });
            }
        }
    });

    const fpFecha = flatpickr("#fecha_cita", {
        locale: "es",
        dateFormat: "Y-m-d",
        minDate: "today",
        allowInput: false,
        altInput: true,
        altFormat: "d F, Y"
    });

    // 3. PREVISUALIZACIÓN DE VEHÍCULO
    const selectVehiculo = document.getElementById('select-vehiculo');
    const contenedorPreview = document.getElementById('contenedor-previsualizacion');

    if (selectVehiculo && contenedorPreview) {
        selectVehiculo.addEventListener('change', function() {
            const opcionSeleccionada = this.options[this.selectedIndex];
            
            if (opcionSeleccionada && opcionSeleccionada.value !== "") {
                const marca = opcionSeleccionada.getAttribute('data-marca');
                const modelo = opcionSeleccionada.getAttribute('data-modelo');
                const color = opcionSeleccionada.getAttribute('data-color');
                const anio = opcionSeleccionada.getAttribute('data-anio');
                const placa = opcionSeleccionada.getAttribute('data-placa');
                let imagen = opcionSeleccionada.getAttribute('data-imagen');

                if (!imagen || imagen.trim() === "") {
                    imagen = `data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100%' height='100%' viewBox='0 0 400 220' style='background:%23e9ecef;'><rect width='400' height='220' fill='%23e9ecef'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='sans-serif' font-size='16' fill='%236c757d'>Vehículo sin fotografía</text></svg>`;
                }

                contenedorPreview.innerHTML = `
                    <div class="card shadow border-0 rounded-3 overflow-hidden text-start mx-auto animate__animated animate__fadeIn" style="max-width: 350px;">
                        <img src="${imagen}" class="card-img-top" alt="${marca} ${modelo}" style="height: 180px; object-fit: cover;">
                        <div class="card-body">
                            <h5 class="card-title fw-bold text-dark mb-1">${marca} ${modelo}</h5>
                            <p class="text-muted small mb-2"><i class="bi bi-hash me-1"></i>Placa: <span class="badge bg-primary px-2">${placa}</span></p>
                            
                            <div class="row g-2 pt-2 border-top mt-2">
                                <div class="col-6 small text-secondary"><strong>Color:</strong> ${color}</div>
                                <div class="col-6 small text-secondary"><strong>Año:</strong> ${anio}</div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                contenedorPreview.innerHTML = `
                    <div class="text-muted py-5 border border-dashed rounded-3 bg-light">
                        <i class="bi bi-image text-secondary-50" style="font-size: 3rem;"></i>
                        <h5 class="mt-3 fw-semibold">Ficha del Vehículo</h5>
                        <p class="small text-muted px-4">Seleccione un vehículo disponible de la lista para previsualizar su fotografía y especificaciones.</p>
                    </div>
                `;
            }
        });

        if (selectVehiculo.value !== "") {
            selectVehiculo.dispatchEvent(new Event('change'));
        }
    }

    // 4. VALIDACIÓN JS EN TIEMPO REAL (Estilo Vehículos)
    const formAgendar = document.getElementById('form-agendar');
    if (formAgendar) {
        const inputs = formAgendar.querySelectorAll('input[required], select[required]');

        inputs.forEach(input => {
            ['input', 'change', 'blur'].forEach(evt => {
                input.addEventListener(evt, () => validarCampoCita(input));
            });
        });

        function validarCampoCita(input) {
            let esValido = true;
            const valor = input.value ? input.value.trim() : '';

            if (valor === '') {
                esValido = false;
            }

            if (input.name === 'fecha_cita') {
                if (!valor) esValido = false;
            }

            if (input.name === 'hora_cita') {
                if (!valor) esValido = false;
            }

            if (input.name === 'cod_catalogo' || input.name === 'cedula_cliente') {
                if (!valor || valor === '') esValido = false;
            }

            if (esValido) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
            return esValido;
        }

        formAgendar.addEventListener('submit', function (e) {
            e.preventDefault();

            let formValido = true;
            inputs.forEach(input => {
                if (!validarCampoCita(input)) formValido = false;
            });

            if (!formValido) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Datos Incompletos o Inválidos',
                        text: 'Por favor, revise los campos marcados en rojo antes de agendar.',
                        confirmButtonColor: '#007bff'
                    });
                }
                return;
            }

            // Confirmación antes de enviar
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¿Confirmar Agendamiento?',
                    text: 'Se procederá a agendar la cita para el vehículo seleccionado.',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#007bff',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Sí, Agendar Cita',
                    cancelButtonText: 'Cancelar',
                    reverseButtons: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        const botonSubmit = document.getElementById('btn-agendar');
                        if (botonSubmit) {
                            botonSubmit.disabled = true;
                            botonSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span> Procesando cita...';
                        }
                        formAgendar.submit();
                    }
                });
            } else {
                formAgendar.submit();
            }
        });
    }

});