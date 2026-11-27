document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    // 1. MENSAJES FLASH SWEETALERT2
    const msgElements = document.querySelectorAll('.flask-msg-data');
    msgElements.forEach(el => {
        const mensaje = el.dataset.message;
        const categoria = el.dataset.category; 

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: categoria === 'success' ? '¡Éxito!' : (categoria === 'warning' ? 'Advertencia' : 'Aviso'),
                text: mensaje,
                icon: categoria === 'error' ? 'error' : (categoria === 'success' ? 'success' : 'info'),
                timer: 3500,
                timerProgressBar: true,
                confirmButtonColor: '#3085d6'
            });
        }
    });

    const tablaClientes = $('#tablaClientes');
    if (tablaClientes.length > 0) {
        tablaClientes.DataTable({
            dom: "<'row mb-3'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
                 "<'row'<'col-sm-12'tr>>" +
                 "<'row mt-3'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
            language: {
                lengthMenu: "Mostrar _MENU_ registros por página",
                zeroRecords: "No se encontraron clientes coincidentes",
                info: "Mostrando página _PAGE_ de _PAGES_",
                infoEmpty: "No hay registros disponibles",
                search: "Buscar Cliente:",
                paginate: { next: "Siguiente", previous: "Anterior" }
            },
            pageLength: 10,
            order: [[2, "asc"]],
            columnDefs: [
                { orderable: false, targets: [0, 7] }
            ]
        });
    }

    // INYECTAR EN MODAL EDITAR
    $(document).on('click', '.btn-editar-cliente', function () {
        var btn       = $(this);
        var cedula    = btn.attr('data-cedula');
        var nombre    = btn.attr('data-nombre');
        var apellido  = btn.attr('data-apellido');
        var telefono  = btn.attr('data-telefono');
        var direccion = btn.attr('data-direccion');
        var correo    = btn.attr('data-correo');
        var fotoUrl   = btn.attr('data-foto');

        $('#editar_cedula').val(cedula);
        $('#editar_nombre').val(nombre);
        $('#editar_apellido').val(apellido);
        $('#editar_telefono').val(telefono);
        $('#editar_direccion').val(direccion);
        $('#editar_correo').val(correo);

        var previewImg = document.getElementById('preview-editar');
        if (fotoUrl && fotoUrl.trim() !== '') {
            previewImg.src = fotoUrl;
            previewImg.style.display = 'block';
        } else {
            previewImg.src = '#';
        }

        $('#form-editar').attr('action', '/clientes/editar/' + cedula);
    });

    var inputFotoEditar = document.getElementById('foto_perfil_editar');
    if (inputFotoEditar) {
        inputFotoEditar.addEventListener('change', function () {
            var previewImg = document.getElementById('preview-editar');
            if (this.files && this.files[0]) {
                var reader = new FileReader();
                reader.onload = function (e) {
                    previewImg.src = e.target.result;
                    previewImg.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // ELIMINAR CLIENTE CON SWEETALERT2
    $(document).on('click', '.btn-eliminar-cliente', function (e) {
        e.preventDefault();
        var cedula = $(this).attr('data-cedula');
        var nombre = $(this).attr('data-nombre');

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: '¿Eliminar Cliente?',
                text: `¿Está seguro de eliminar al cliente "${nombre}" (C.I. ${cedula}) de forma permanente? Esta acción es irreversible.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, Eliminar',
                cancelButtonText: 'Cancelar',
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    var form = document.createElement('form');
                    form.method = 'POST';
                    form.action = '/clientes/eliminar/' + cedula;
                    document.body.appendChild(form);
                    form.submit();
                }
            });
        }
    });

    // VALIDACIÓN EN TIEMPO REAL Y CONFIRMACIÓN DEL FORMULARIO DE EDICIÓN DE CLIENTE
    const formEditar = document.getElementById('form-editar');
    if (formEditar) {
        const inputsEdit = formEditar.querySelectorAll('input[required]');

        inputsEdit.forEach(input => {
            input.addEventListener('input', function() {
                if (this.name === 'telefono') {
                    this.value = this.value.replace(/\D/g, '');
                }
                if (this.name === 'nombre' || this.name === 'apellido') {
                    this.value = this.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
                }
                if (this.name === 'correo') {
                    this.value = this.value.replace(/\s/g, '');
                }
                if (this.name === 'direccion') {
                    this.value = this.value.replace(/[<>"'`;]/g, '');
                }
                validarCampoEditarCliente(this);
            });

            input.addEventListener('blur', function() {
                validarCampoEditarCliente(this);
            });
        });

        function validarCampoEditarCliente(input) {
            let esValido = true;
            const valor = input.value.trim();

            if (valor === "") esValido = false;

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

            if (input.name === 'correo') {
                const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!regexEmail.test(valor) || valor.length > 60) esValido = false;
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

        formEditar.addEventListener('submit', function(e) {
            e.preventDefault();

            let formValido = true;
            inputsEdit.forEach(input => {
                if (!validarCampoEditarCliente(input)) formValido = false;
            });

            if (!formValido) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Datos Inválidos',
                        text: 'Revise los campos en rojo antes de guardar los cambios del cliente.',
                        confirmButtonColor: '#ffc107'
                    });
                }
                return;
            }

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¿Guardar Cambios?',
                    text: 'Se actualizarán la información del cliente.',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#ffc107',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Sí, Guardar',
                    cancelButtonText: 'Cancelar',
                    reverseButtons: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        formEditar.submit();
                    }
                });
            } else {
                formEditar.submit();
            }
        });
    }

});


