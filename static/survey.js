// static/survey.js
document.addEventListener('DOMContentLoaded', function() {
    // Mostrar/ocultar detalles de ejercicios
    document.querySelectorAll('input[name="exercise_types"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const details = this.parentElement.querySelector('.exercise-details');
            details.style.display = this.checked ? 'grid' : 'none';
        });
        
        // Establecer estado inicial
        const details = checkbox.parentElement.querySelector('.exercise-details');
        details.style.display = checkbox.checked ? 'grid' : 'none';
    });

    // Hacer la lista de grupos musculares ordenable
    const sortableList = document.querySelector('.sortable-list');
    new Sortable(sortableList, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        onEnd: function() {
            // Actualizar los valores de prioridad
            updatePriorities();
        }
    });
});

function updatePriorities() {
    const items = document.querySelectorAll('.muscle-group-item input:checked');
    items.forEach((item, index) => {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = `priority_${item.value}`;
        hiddenInput.value = index + 1;
        item.parentElement.appendChild(hiddenInput);
    });
}