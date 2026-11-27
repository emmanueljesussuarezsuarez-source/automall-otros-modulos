
document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    // 1. MENSAJES FLASH SWEETALERT2
    const msgElements = document.querySelectorAll('.flask-msg-data');
    msgElements.forEach(el => {
        const mensaje = el.dataset.message;
        const categoria = el.dataset.category; 

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: categoria === 'success' ? '¡Logrado!' : 'Aviso',
                text: mensaje,
                icon: categoria === 'error' ? 'error' : (categoria === 'success' ? 'success' : 'info'),
                timer: 4000,
                timerProgressBar: true,
                confirmButtonColor: '#198754'
            });
        }
    });

    // 2. FILTRADO Y SANITIZACIÓN EN TIEMPO REAL AL ESCRIBIR
    const form = document.getElementById('form-registro') || document.querySelector('form');

    if (form) {
        const inputs = form.querySelectorAll('input[required]');

        inputs.forEach(input => {
            input.addEventListener('input', function() {
                // Restricciones activas de escritura por tipo de campo
                if (this.name === 'cedula' || this.name === 'telefono') {
                    this.value = this.value.replace(/\D/g, ''); // Solo números
                }
                if (this.name === 'nombre' || this.name === 'apellido') {
                    this.value = this.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, ''); // Solo letras y espacios
                }
                if (this.name === 'email') {
                    this.value = this.value.replace(/\s/g, ''); // Sin espacios
                }
                if (this.name === 'direccion') {
                    this.value = this.value.replace(/[<>"'`;]/g, ''); // Sin caracteres peligrosos de script
                }
                validarCampoCliente(this);
            });

            input.addEventListener('blur', function() {
                validarCampoCliente(this);
            });
        });

        function validarCampoCliente(input) {
            let esValido = true;
            const valor = input.value.trim();

            if (valor === "") esValido = false;

            if (input.name === 'cedula') {
                const regexCedula = /^\d{6,10}$/;
                if (!regexCedula.test(valor)) esValido = false;
            }

            if (input.name === 'nombre' || input.name === 'apellido') {
                const regexTexto = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,40}$/;
                if (!regexTexto.test(valor)) esValido = false;
            }

            if (input.name === 'telefono') {
                const regexTelefono = /^\d{11}$/;
                if (!regexTelefono.test(valor)) esValido = false;
            }

            if (input.name === 'direccion') {
                if (valor.length < 5 || valor.length > 150) esValido = false;
            }

            if (input.name === 'email') {
                const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!regexEmail.test(valor) || valor.length > 60) esValido = false;
            }

            if (input.name === 'password') {
                if (valor.length < 8 || valor.length > 50) esValido = false;
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

        form.addEventListener('submit', function (e) {
            e.preventDefault();

            let formValido = true;
            inputs.forEach(input => {
                if (!validarCampoCliente(input)) formValido = false;
            });

            if (!formValido) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Datos Inválidos',
                        text: 'Revise los campos en rojo antes de enviar el formulario.',
                        confirmButtonColor: '#198754'
                    });
                }
                return;
            }

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¿Confirmar Registro?',
                    text: 'Se procederá a crear la cuenta de cliente con los datos suministrados.',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#198754',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Sí, Registrar',
                    cancelButtonText: 'Cancelar',
                    reverseButtons: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        form.submit();
                    }
                });
            } else {
                form.submit();
            }
        });
    }
});