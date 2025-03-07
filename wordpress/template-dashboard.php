<?php
/*
Template Name: Dashboard Page
*/
get_header(); ?>

<div id="dashboard-container">
    <div class="month-year-selector" style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 20px;">
        <button id="prevMonth"><</button>
        <span id="displayMonthYear"></span>
        <button id="nextMonth">></button>
        <select id="timesheetSelect"></select>
    </div>

    <div class="grid-container">
        <div class="grid-item">
            <h3>Working Onsite/Office Percentage</h3>
            <div id="onsiteOfficePercentage"></div>
        </div>
        <div class="grid-item" id="submissionOrOffDays">
            <!-- Content will be dynamically set -->
        </div>
        <div class="grid-item">
            <h3>PS/MA/Internal/Pre-Sales Percentage</h3>
            <div id="psMaInternalPresalesPercentage"></div>
        </div>
        <div class="grid-item">
            <h3>Customer Type - <span id="selectedJobType"></span></h3>
            <div class="job-type-buttons">
                <button onclick="changeJobType('PS')">PS</button>
                <button onclick="changeJobType('Pre-Sales')">Pre-Sales</button>
                <button onclick="changeJobType('MA')">MA</button>
            </div>
            <div id="customerType" class="customer-type-grid"></div>
        </div>
        <div class="grid-item grid-item-span-2">
            <h3>This Month's Projects</h3>
            <div style="display: flex; gap: 10px;">
                <button onclick="sortTable('alpha')">Sort by Customer Name</button>
                <button onclick="sortTable('percentage')">Sort by Percentage</button>
            </div>
            <table id="projectsTable">
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Project Name</th>
                        <th>SO</th>
                        <th>Frequency</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
</div>

<style>
.grid-container {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin-top: 20px;
}
.grid-item {
    border: 1px solid #ccc;
    padding: 10px;
}
.grid-item-span-2 {
    grid-column: span 2;
}
.customer-type-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 5px;
}
.month-year-selector button, .month-year-selector select {
    padding: 5px 10px;
}
</style>

<script>
let currentYear = <?php echo date('Y'); ?>;
let currentMonth = <?php echo date('n'); ?>;
let currentJobType = 'PS';
let currentTimesheet = 'SSS_Team';

function updateDisplay() {
    document.getElementById('displayMonthYear').textContent = `${currentYear} ${String(currentMonth).padStart(2, '0')}`;
    fetchStatistics();
}

function fetchStatistics() {
    fetch(`http://192.168.168.14:5000/api/statistics?year=${currentYear}&month=${currentMonth}&job_type=${currentJobType}&timesheet_file=${currentTimesheet}`)
        .then(response => response.json())
        .then(data => {
            // Populate timesheet dropdown
            const select = document.getElementById('timesheetSelect');
            select.innerHTML = '<option value="SSS_Team">SSS Team</option>';
            data.timesheet_files.forEach(file => {
                const option = document.createElement('option');
                option.value = file.replace(' ', '_');
                option.text = file;
                if (file.replace(' ', '_') === currentTimesheet) option.selected = true;
                select.appendChild(option);
            });

            // Onsite/Office Percentage
            document.getElementById('onsiteOfficePercentage').innerHTML = `
                <p>Onsite: ${data.onsite_percentage.toFixed(2)}%</p>
                <p>Office: ${data.office_percentage.toFixed(2)}%</p>
            `;

            // Toggle between Timesheet Submission and Off Days
            const submissionOrOffDays = document.getElementById('submissionOrOffDays');
            if (currentTimesheet === 'SSS_Team') {
                submissionOrOffDays.innerHTML = `
                    <h3>Timesheet Submission</h3>
                    <div id="timesheetSubmission">
                        <p>Number of people who have included their timesheet this month: ${data.timesheet_count}</p>
                    </div>
                `;
            } else {
                submissionOrOffDays.innerHTML = `
                    <h3>Off Days</h3>
                    <div id="offDays">
                        <p>Annual Leave (AL): ${data.off['AL']}</p>
                        <p>Casual Leave (CL): ${data.off['CL']}</p>
                        <p>Sick Leave (SL): ${data.off['SL']}</p>
                        <p>Public Holiday: ${data.off['Public Holiday']}</p>
                    </div>
                `;
            }

            // PS/MA/Internal/Pre-Sales Percentage
            document.getElementById('psMaInternalPresalesPercentage').innerHTML = `
                <p>PS: ${data.ps_percentage.toFixed(2)}%</p>
                <p>MA: ${data.ma_percentage.toFixed(2)}%</p>
                <p>Internal: ${data.internal_percentage.toFixed(2)}%</p>
                <p>Pre-Sales: ${data.presales_percentage.toFixed(2)}%</p>
            `;

            // Customer Type
            document.getElementById('selectedJobType').textContent = currentJobType;
            let customerHtml = '';
            for (let [customer, types] of Object.entries(data.customer_data)) {
                if (customer !== 'TBC' || (customer === 'TBC' && currentJobType === 'MA')) {
                    customerHtml += `<div class="customer-type-item"><p>${customer}: ${types[currentJobType]}</p></div>`;
                }
            }
            document.getElementById('customerType').innerHTML = customerHtml;

            // This Month's Projects
            const tbody = document.getElementById('projectsTable').getElementsByTagName('tbody')[0];
            tbody.innerHTML = '';
            data.monthly_projects.forEach(project => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${project.customer}</td>
                    <td>${project.name}</td>
                    <td>${project.so}</td>
                    <td>${project.frequency}</td>
                    <td>${project.percentage.toFixed(2)}%</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching statistics:', error));
}

document.getElementById('prevMonth').addEventListener('click', () => {
    currentMonth--;
    if (currentMonth < 1) {
        currentMonth = 12;
        currentYear--;
    }
    updateDisplay();
});

document.getElementById('nextMonth').addEventListener('click', () => {
    currentMonth++;
    if (currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
    }
    updateDisplay();
});

document.getElementById('timesheetSelect').addEventListener('change', () => {
    currentTimesheet = document.getElementById('timesheetSelect').value;
    fetchStatistics();
});

function changeJobType(jobType) {
    currentJobType = jobType;
    fetchStatistics();
}

function sortTable(criteria) {
    const tbody = document.getElementById('projectsTable').getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.rows);

    rows.sort((a, b) => {
        if (criteria === 'alpha') {
            return a.cells[0].textContent.localeCompare(b.cells[0].textContent);
        } else if (criteria === 'percentage') {
            return parseFloat(b.cells[4].textContent) - parseFloat(a.cells[4].textContent);
        }
    });

    rows.forEach(row => tbody.appendChild(row));
}

// Initial load
updateDisplay();
</script>

<?php get_footer(); ?>