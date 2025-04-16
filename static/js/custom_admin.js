// Initialize DataTable
$(document).ready(function() {
    const table = $('#usersTable').DataTable({
        ajax: {
            url: '/api/users/',
            error: function (xhr, error, thrown) {
                console.error('DataTable error:', error);
                alert('Error loading user data. Please try refreshing the page.');
            }
        },
        columns: [
            { data: 'id' },
            { data: 'username' },
            { data: 'full_name' },
            { data: 'email' },
            { data: 'role' },
            {
                data: null,
                render: function(data, type, row) {
                    return `
                        <button class="btn btn-primary btn-sm update-role" data-id="${row.id}">
                            <i class="fas fa-user-edit"></i> Update Role
                        </button>
                        <button class="btn btn-info btn-sm download-pdf" data-id="${row.id}">
                            <i class="fas fa-download"></i> Download PDF
                        </button>
                    `;
                }
            }
        ],
        order: [[0, 'desc']],
        pageLength: 10,
        responsive: true,
        processing: true,  
        language: {
            processing: "Loading...",
            zeroRecords: "No matching records found",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            infoEmpty: "Showing 0 to 0 of 0 entries",
            infoFiltered: "(filtered from _MAX_ total entries)"
        }
    });

    // Handle role update button click
    $('#usersTable').on('click', '.update-role', function() {
        const userId = $(this).data('id');
        $('#userId').val(userId);
        $('#updateRoleModal').modal('show');
    });

    // Handle PDF download button click
    $('#usersTable').on('click', '.download-pdf', function() {
        const userId = $(this).data('id');
        window.location.href = `/api/user-pdf/${userId}/`;
    });

    // Save role changes
    $('#saveRoleBtn').click(function() {
        const userId = $('#userId').val();
        const newRole = $('#roleSelect').val();

        $.ajax({
            url: `/admin_dash/update_role/${userId}/`,
            method: 'POST',
            data: {
                role: newRole,
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                $('#updateRoleModal').modal('hide');
                table.ajax.reload();
                loadCharts(); // Reload charts to reflect changes
            },
            error: function(xhr, status, error) {
                alert('Error updating role: ' + error);
            }
        });
    });

    // Load charts
    loadCharts();
});

function loadCharts() {
    $.get('/api/user-stats/', function(data) {
        createUserJoinChart(data.user_joins);
        createRoleDistributionChart(data.role_distribution);
    });

    $.get('/api/depression-stats/', function(data) {
        createDepressionPieChart(data.depression_levels);
    });

    $.get('/api/appointment-stats/', function(data) {
        createAppointmentChart(data.appointments);
    });
}

function createUserJoinChart(data) {
    const ctx = document.getElementById('userJoinChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => new Date(item.date).toLocaleDateString()),
            datasets: [{
                label: 'New Users',
                data: data.map(item => item.count),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function createDepressionPieChart(data) {
    const ctx = document.getElementById('depressionPieChart').getContext('2d');
    const colors = [
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0',
        '#9966FF'
    ];
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(item => {
                const levels = {
                    '0': 'None',
                    '1': 'Mild',
                    '2': 'Moderate',
                    '3': 'Moderately Severe',
                    '4': 'Severe'
                };
                return levels[item.depression_level];
            }),
            datasets: [{
                data: data.map(item => item.count),
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function createAppointmentChart(data) {
    const ctx = document.getElementById('appointmentChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.doctor__user__first_name),
            datasets: [{
                label: 'Number of Appointments',
                data: data.map(item => item.count),
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function createRoleDistributionChart(data) {
    const ctx = document.getElementById('roleDistributionChart').getContext('2d');
    const colors = [
        '#FF6384',
        '#36A2EB',
        '#FFCE56'
    ];
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.role.charAt(0).toUpperCase() + item.role.slice(1)),
            datasets: [{
                data: data.map(item => item.count),
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}
