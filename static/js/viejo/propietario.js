async function verFlota(cedula, nombre) {
    document.getElementById('nombrePropietarioFlota').innerText = nombre;
    const contenedor = document.getElementById('contenedorFlota');
    
    // Spinner de carga inicial
    contenedor.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-muted small">Consultando inventario de la flota...</p>
        </div>`;
    
    // Mostrar el modal
    const modalFlota = new bootstrap.Modal(document.getElementById('modalFlota'));
    modalFlota.show();

    try {
        // Consultamos a la nueva ruta que usa la Vista vw_vehiculos_propietarios_detalle
        const response = await fetch(`/propietarios/vehiculos/${cedula}`);
        const vehiculos = await response.json();
        
        contenedor.innerHTML = ''; // Limpiar spinner

        if (vehiculos.length === 0) {
            contenedor.innerHTML = `
                <div class="col-12 text-center p-4">
                    <i class="bi bi-info-circle fs-1 text-muted"></i>
                    <p class="text-muted mt-2">Este propietario no tiene vehículos registrados actualmente.</p>
                </div>`;
            return;
        }

        // Construir las tarjetas de los vehículos
        vehiculos.forEach(v => {
            const imgPath = v.imagen_url ? `/static/${v.imagen_url}` : '/static/img/no-photo.jpg';
            contenedor.innerHTML += `
                <div class="col-md-6">
                    <div class="card h-100 border-0 shadow-sm bg-white">
                        <div class="row g-0">
                            <div class="col-4">
                                <img src="${imgPath}" class="img-fluid rounded-start h-100" style="object-fit: cover; min-height: 110px;">
                            </div>
                            <div class="col-8">
                                <div class="card-body p-2">
                                    <div class="fw-bold text-primary mb-1 small">${v.nombre_marca} ${v.nombre_modelo}</div>
                                    <div class="mb-1"><span class="badge bg-dark" style="font-size: 0.7rem;">${v.placa}</span></div>
                                    <div class="small text-muted" style="font-size: 0.75rem;">
                                        Año: ${v.anio} | Color: ${v.color}
                                    </div>
                                    <div class="text-success fw-bold mt-1">$${parseFloat(v.precio || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
    } catch (error) {
        contenedor.innerHTML = '<div class="col-12 text-center text-danger p-4">Error al conectar con la base de datos.</div>';
    }
}

// --- 1. FUNCIÓN DE ELIMINACIÓN POR AJAX ---
async function confirmarEliminarPropietario(cedula) {
    const result = await Swal.fire({
        title: '¿Eliminar propietario?',
        text: "Se eliminará al propietario permanentemente con CI/RIF: " + cedula,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true
    });

    if (result.isConfirmed) {
        // Obtenemos la URL del formulario que ya tienes en el HTML
        const formulario = document.getElementById('form-eliminar-' + cedula);
        const url = formulario.action;

        // Mostramos una alerta de "Procesando"
        Swal.fire({
            title: 'Eliminando...',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });

        try {
            // Enviamos la petición al servidor
            const response = await fetch(url, { method: 'POST' });
            const data = await response.json();

            if (data.status === 'success') {
                // SI TODO SALIÓ BIEN: Alerta de éxito pura
                Swal.fire({
                    icon: 'success',
                    title: '¡Logrado!',
                    text: data.message,
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    window.location.reload(); // Recargamos para ver los cambios en la tabla
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message
                });
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Error de red',
                text: 'No se pudo comunicar con el servidor.'
            });
        }
    }
}

// EL RESTO DEL CÓDIGO (DOMContentloaded, Validaciones, Registro, Editar) SE MANTIENE IGUAL

document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. LÓGICA DEL MODAL (Carga de datos al editar) ---
    const botonesEditar = document.querySelectorAll('.btn-editar');
    botonesEditar.forEach(boton => {
        boton.addEventListener('click', function() {
            const d = this.dataset; 
            document.getElementById('edit_cedula_original').value = d.cedula;
            document.getElementById('edit_cedula').value = d.cedula;
            document.getElementById('edit_nombre').value = d.nombre;
            document.getElementById('edit_telefono').value = d.telefono;
            document.getElementById('edit_correo').value = d.correo;
            document.getElementById('edit_direccion').value = d.direccion;
            document.getElementById('edit_tipo').value = d.tipo;
            document.getElementById('edit_estado').value = d.estado;
            
            // Re-validar visualmente al abrir
            const camposModal = document.querySelectorAll('#modalEditar .form-control');
            camposModal.forEach(i => {
                validarInput(i);
            });
        });
    });

    // --- 2. VALIDACIÓN VISUAL Y LÓGICA ---
    const validarInput = (input) => {
        const valor = input.value.trim();
        const name = input.name;
        let esValido = true;
        let mensajeError = "";

        if (valor === "") {
            esValido = false;
            mensajeError = "Este campo es obligatorio.";
        } else {
            if (name === 'cedula') {
                esValido = /^[0-9]{6,12}$/.test(valor); 
                mensajeError = "Cédula inválida (6 a 12 números).";
            } else if (name === 'razon_social') {
                esValido = /^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]{3,50}$/.test(valor);
                mensajeError = "Solo letras (3 a 50 caracteres).";
            } else if (name === 'telefono') {
                esValido = /^[0-9]{10,15}$/.test(valor);
                mensajeError = "Teléfono inválido (10 a 15 números).";
            } 
            // --- VALIDACIÓN DE CORREO ---
            else if (name === 'correo') {
                // Solo permite letras, números, puntos, guiones y el @. Máximo 50 caracteres.
                const regexCorreo = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
                if (valor.length > 50) {
                    esValido = false;
                    mensajeError = "El correo es muy largo (Máximo 50).";
                } else if (!regexCorreo.test(valor)) {
                    esValido = false;
                    mensajeError = "Formato inválido (Solo letras, números, . y -).";
                }
            } 
            // --- VALIDACIÓN DE DIRECCIÓN ---
            else if (name === 'direccion') {
                // Permite letras, números, espacios y los caracteres: . , # - /
                const regexDir = /^[a-zA-Z0-9ñÑáéíóúÁÉÍÓÚ\s.,#/-]+$/;
                if (valor.length < 5 || valor.length > 100) {
                    esValido = false;
                    mensajeError = "Debe tener entre 5 y 100 caracteres.";
                } else if (!regexDir.test(valor)) {
                    esValido = false;
                    mensajeError = "No se permiten símbolos especiales extraños.";
                }
            }
        }

        // --- GESTIÓN VISUAL DEL FEEDBACK ---
        let feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.style.fontSize = '0.85em';
            input.parentNode.appendChild(feedback);
        }

        if (esValido) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            feedback.style.display = 'none';
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            feedback.innerText = mensajeError;
            feedback.style.display = 'block';
        }
        return esValido;
    };

    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('input', () => validarInput(input));
        input.addEventListener('blur', () => validarInput(input));
    });

    const validarFormularioCompleto = (form) => {
        let formValido = true;
        const campos = form.querySelectorAll('input[required], textarea[required], select[required]');
        campos.forEach(campo => {
            if (!validarInput(campo)) formValido = false;
        });

        if (!formValido) {
            Swal.fire({
                icon: 'error',
                title: 'Datos inválidos',
                text: 'Por favor, revise los campos marcados en rojo.',
                confirmButtonColor: '#d33'
            });
        }
        return formValido;
    };

    // --- 3. REGISTRO (AJAX) ---
    const formRegistro = document.querySelector('form[action*="registro"]');
    if (formRegistro) {
        formRegistro.addEventListener('submit', async function(e) {
            e.preventDefault(); 
            if (!validarFormularioCompleto(this)) return;

            Swal.fire({
                title: 'Registrando...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });

            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: new FormData(this)
                });
                const result = await response.json();
                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Registrado!',
                        text: result.message,
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.href = "/propietarios/lista"; 
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Error', text: result.message });
                }
            } catch (error) {
                Swal.fire({ icon: 'error', title: 'Error fatal', text: 'Error de conexión.' });
            }
        });
    }

    // --- 4. EDITAR (AJAX) ---
    const formEditar = document.querySelector('#modalEditar form');
    if (formEditar) {
        formEditar.addEventListener('submit', async function(e) {
            e.preventDefault(); 
            if (!validarFormularioCompleto(this)) return;

            Swal.fire({
                title: 'Actualizando...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });

            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: new FormData(this)
                });
                const result = await response.json();
                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Actualizado!',
                        text: result.message,
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.reload(); 
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Error', text: result.message });
                }
            } catch (error) {
                Swal.fire({ icon: 'error', title: 'Error', text: 'Error de comunicación.' });
            }
        });
    }
});