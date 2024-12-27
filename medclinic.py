from flask import Flask, render_template, redirect, url_for, request, send_file
import sqlite3
from docxtpl import DocxTemplate
import datetime
import openpyxl

app = Flask(__name__)

# --- Функции для работы с базой данных ---
def execute_query(query, params=None, fetchone=False, commit=False):
    """Выполняет SQL-запрос к базе данных и возвращает результат."""
    conn = sqlite3.connect('medclinic.db')
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    if commit:
        conn.commit()
    result = cursor.fetchone() if fetchone else cursor.fetchall()
    conn.close()
    return result


def get_services_from_db():
    """Возвращает список всех услуг."""
    return execute_query("SELECT * FROM Services")


def get_service_from_db(service_id):
    """Возвращает информацию об услуге по ID."""
    return execute_query("SELECT * FROM Services WHERE id = ?", (service_id,), fetchone=True)


def get_patients_from_db():
    """Возвращает список всех пациентов."""
    return execute_query("SELECT * FROM Patients")


def get_patient_from_db(patient_id):
    """Возвращает информацию о пациенте по ID."""
    return execute_query("SELECT * FROM Patients WHERE id = ?", (patient_id,), fetchone=True)


def get_patient_with_visits_from_db(patient_id):
    """Возвращает информацию о пациенте и его посещениях."""
    query = """
        SELECT 
            p.id, p.FIO, p.DateOfBirth, p.PhoneNumber, p.Address, p.InsurancePolicy,
            a.Date, a.Time, e.FIO, a.Complaints, a.PreliminaryDiagnosis
        FROM Patients p
        LEFT JOIN Appointments a ON p.id = a.id_patient
        LEFT JOIN Employees e ON a.id_doctor = e.id
        WHERE p.id = ?
    """
    visits = execute_query(query, (patient_id,))

    if not visits:  # Если нет посещений, но есть пациент
        patient = get_patient_from_db(patient_id)
        if patient:
            return [patient + (None, None, None, None, None,)]  # Возвращаем данные пациента с None для посещений
        else:
            return None
    return visits


def get_employees_from_db():
    """Возвращает список всех сотрудников."""
    return execute_query("SELECT * FROM Employees")


def get_employee_from_db(employee_id):
    """Возвращает информацию о сотруднике по ID."""
    return execute_query("SELECT * FROM Employees WHERE id = ?", (employee_id,), fetchone=True)


def get_appointments_from_db():
    """Возвращает список всех приемов."""
    query = """
        SELECT Appointments.id, Appointments.Date, Appointments.Time, Employees.FIO, Patients.FIO 
        FROM Appointments 
        JOIN Employees ON Appointments.id_doctor = Employees.id 
        JOIN Patients ON Appointments.id_patient = Patients.id
    """
    return execute_query(query)


def get_appointment_from_db(appointment_id):
    """Возвращает информацию о приеме по ID."""
    query = """
        SELECT Appointments.id, Appointments.Date, Appointments.Time, Employees.FIO, Patients.FIO 
        FROM Appointments 
        JOIN Employees ON Appointments.id_doctor = Employees.id 
        JOIN Patients ON Appointments.id_patient = Patients.id 
        WHERE Appointments.id = ?
    """
    return execute_query(query, (appointment_id,), fetchone=True)


def get_payments_from_db():
    """Возвращает список всех платежей."""
    query = """
        SELECT Payments.id, Payments.Date, Payments.payment_time, Patients.FIO, Services.Name, Payments.Summ, 
        Employees.FIO, Services.Code 
        FROM Payments 
        JOIN Patients ON Payments.id_patient = Patients.id 
        JOIN Services ON Payments.id_service = Services.id 
        JOIN Employees ON Payments.employee_id = Employees.id
    """
    return execute_query(query)


def get_payment_from_db(payment_id):
    """Возвращает информацию о платеже по ID."""
    query = """
        SELECT Payments.id, Payments.Date, Payments.payment_time, Patients.FIO, Services.Name, Payments.Summ, 
        Employees.FIO, Services.Code 
        FROM Payments 
        JOIN Patients ON Payments.id_patient = Patients.id 
        JOIN Services ON Payments.id_service = Services.id 
        JOIN Employees ON Payments.employee_id = Employees.id
        WHERE Payments.id = ?
    """
    return execute_query(query, (payment_id,), fetchone=True)


def get_clinic_info():
    """Возвращает информацию о клинике."""
    return execute_query("SELECT * FROM ClinicInfo", fetchone=True)


# --- Функции для генерации документов ---
def generate_payment_check(payment_data, clinic_info):
    """Генерирует чек об оплате."""
    template_path = 'templates/documents/cheque.docx'
    template = DocxTemplate(template_path)

    if payment_data:
        context = {
            'CLINIC_NAME': clinic_info[1] if clinic_info else "Неизвестно",
            'CLINIC_ADDRESS': clinic_info[2] if clinic_info else "Неизвестно",
            'CLINIC_PHONE': clinic_info[3] if clinic_info else "Неизвестно",
            'CHECK_NUMBER': payment_data[0] if payment_data else "Неизвестно",
            'PAYMENT_DATE': payment_data[1] if payment_data else "Неизвестно",
            'PAYMENT_TIME': payment_data[2] if payment_data else "Неизвестно",
            'PATIENT_FULLNAME': payment_data[3] if payment_data else "Неизвестно",
            'PATIENT_ID': payment_data[0] if payment_data else "Неизвестно",
            'SERVICE_NAME': payment_data[4] if payment_data else "Неизвестно",
            'SERVICE_CODE': payment_data[7] if payment_data else "Неизвестно",
            'SERVICE_COST': payment_data[5] if payment_data else "Неизвестно",
            'EMPLOYEE_NAME': payment_data[6] if payment_data else "Неизвестно"
        }
    else:
        context = {
            'CLINIC_NAME': None,
            'CLINIC_ADDRESS': None,
            'CLINIC_PHONE': None,
            'CHECK_NUMBER': None,
            'PAYMENT_DATE': None,
            'PAYMENT_TIME': None,
            'PATIENT_FULLNAME': None,
            'PATIENT_ID': None,
            'SERVICE_NAME': None,
            'SERVICE_CODE': None,
            'SERVICE_COST': None,
            'EMPLOYEE_NAME': None
        }
    output_path = f'templates/documents/payment_{payment_data[0] if payment_data else "unknown"}_cheque.docx'
    template.render(context)
    template.save(output_path)
    return output_path


def generate_workload_report(start_date, end_date, employee_id):
    """Генерирует отчет о загрузке персонала."""
    query = """
        SELECT a.Date, a.Time, p.FIO AS patient_name, e.FIO AS employee_name FROM Appointments a
        JOIN Patients p ON a.id_patient = p.id
        JOIN Employees e ON a.id_doctor = e.id
        WHERE a.Date BETWEEN ? AND ?
    """
    params = (start_date, end_date)
    if employee_id:
        query += " AND e.id = ? "
        params = (start_date, end_date, employee_id)

    appointments = execute_query(query, params)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Дата", "Время", "Пациент", "Сотрудник"])
    for appointment in appointments:
        ws.append([appointment[0], appointment[1], appointment[2], appointment[3]])

    output_path = f'templates/documents/workload_report_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.xlsx'
    wb.save(output_path)
    return output_path

# --- Маршруты ---
@app.route('/')
def index():
    """Перенаправляет на страницу списка пациентов."""
    return redirect(url_for('patients_list'))


@app.route('/patients')
def patients_list():
    """Отображает список пациентов."""
    patients = get_patients_from_db()
    return render_template('patients/patients_list.html', patients=patients)


@app.route('/patients/<int:id>')
def patient_details(id):
    """Отображает детали пациента и его посещения."""
    patient_data = get_patient_with_visits_from_db(id)
    if patient_data:
        patient = patient_data[0]
        visits = patient_data
        return render_template('patients/patient_details.html', patient=patient, visits=visits)
    else:
        return render_template('patients/patient_details.html', patient=None, visits=None)


@app.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
def edit_patient(id):
    """Отображает форму для редактирования пациента и обрабатывает ее."""
    patient = get_patient_from_db(id)
    if request.method == 'POST':
        fio = request.form['fio']
        date_of_birth = request.form['date_of_birth']
        phone = request.form['phone']
        address = request.form['address']
        insurance_policy = request.form['insurance_policy']
        query = "UPDATE Patients SET FIO = ?, DateOfBirth = ?, PhoneNumber = ?, Address = ?, InsurancePolicy = ? WHERE id = ?"
        execute_query(query, (fio, date_of_birth, phone, address, insurance_policy, id), commit=True)
        return redirect(url_for('patient_details', id=id))
    return render_template('patients/edit_patient.html', patient=patient)


@app.route('/employees')
def employees_list():
    """Отображает список сотрудников."""
    employees = get_employees_from_db()
    return render_template('employees/employees_list.html', employees=employees)


@app.route('/employees/<int:id>')
def employee_details(id):
    """Отображает детали сотрудника."""
    employee = get_employee_from_db(id)
    return render_template('employees/employee_details.html', employee=employee)


@app.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
def edit_employee(id):
    """Отображает форму для редактирования сотрудника и обрабатывает ее."""
    employee = get_employee_from_db(id)
    if request.method == 'POST':
        fio = request.form['fio']
        position = request.form['position']
        phone = request.form['phone']
        specialization = request.form['specialization']
        query = "UPDATE Employees SET FIO = ?, Position = ?, PhoneNumber = ?, Specialization = ? WHERE id = ?"
        execute_query(query, (fio, position, phone, specialization, id), commit=True)
        return redirect(url_for('employee_details', id=id))
    return render_template('employees/edit_employee.html', employee=employee)


@app.route('/services')
def services_list():
    """Отображает список услуг."""
    services = get_services_from_db()
    return render_template('services/services_list.html', services=services)


@app.route('/services/<int:id>')
def service_details(id):
    """Отображает детали услуги."""
    service = get_service_from_db(id)
    return render_template('services/service_details.html', service=service)


@app.route('/services/<int:id>/edit', methods=['GET', 'POST'])
def edit_service(id):
    """Отображает форму для редактирования услуги и обрабатывает ее."""
    service = get_service_from_db(id)
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        cost = request.form['cost']
        description = request.form['description']
        detailed_description = request.form['detailed_description']
        query = "UPDATE Services SET Name = ?, Code = ?, Cost = ?, Description = ?, DetailedDescription = ? WHERE id = ?"
        execute_query(query, (name, code, cost, description, detailed_description, id), commit=True)
        return redirect(url_for('service_details', id=id))
    return render_template('services/edit_service.html', service=service)


@app.route('/appointments')
def appointments_list():
    """Отображает список приемов."""
    appointments = get_appointments_from_db()
    return render_template('appointments/appointments_list.html', appointments=appointments)


@app.route('/appointments/<int:id>')
def appointment_details(id):
    """Отображает детали приема."""
    appointment = get_appointment_from_db(id)
    return render_template('appointments/appointment_details.html', appointment=appointment)


@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
def edit_appointment(id):
    """Отображает форму для редактирования приема и обрабатывает ее."""
    appointment = get_appointment_from_db(id)
    employees = get_employees_from_db()
    patients = get_patients_from_db()
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        doctor = request.form['doctor']
        patient = request.form['patient']
        query = "UPDATE Appointments SET id_doctor = ?, id_patient = ?, Date = ?, Time = ? WHERE id = ?"
        execute_query(query, (doctor, patient, date, time, id), commit=True)
        return redirect(url_for('appointment_details', id=id))
    return render_template('appointments/edit_appointment.html', appointment=appointment, employees=employees,
                           patients=patients)


@app.route('/payments')
def payments_list():
    """Отображает список платежей."""
    payments = get_payments_from_db()
    return render_template('payments/payments_list.html', payments=payments)


@app.route('/payments/<int:id>')
def payment_details(id):
    """Отображает детали платежа."""
    payment = get_payment_from_db(id)
    return render_template('payments/payment_details.html', payment=payment)


@app.route('/payments/<int:id>/edit', methods=['GET', 'POST'])
def edit_payment(id):
    """Отображает форму для редактирования платежа и обрабатывает ее."""
    payment = get_payment_from_db(id)
    services = get_services_from_db()
    patients = get_patients_from_db()
    employees = get_employees_from_db()
    if request.method == 'POST':
        date = request.form['date']
        payment_time = request.form['time']
        patient = request.form['patient']
        service = request.form['service']
        summ = request.form['summ']
        employee = request.form['employee']
        query = "UPDATE Payments SET id_patient = ?, id_service = ?, Date = ?, Summ = ?, payment_time = ?, employee_id = ? WHERE id = ?"
        execute_query(query, (patient, service, date, summ, payment_time, employee, id), commit=True)
        return redirect(url_for('payment_details', id=id))
    return render_template('payments/edit_payment.html', payment=payment, services=services, patients=patients,
                           employees=employees)


@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    """Отображает форму для добавления пациента и обрабатывает ее."""
    if request.method == 'POST':
        fio = request.form['fio']
        date_of_birth = request.form['date_of_birth']
        phone = request.form['phone']
        address = request.form['address']
        insurance_policy = request.form['insurance_policy']
        query = "INSERT INTO Patients (FIO, DateOfBirth, PhoneNumber, Address, InsurancePolicy) VALUES (?, ?, ?, ?, ?)"
        execute_query(query, (fio, date_of_birth, phone, address, insurance_policy), commit=True)
        return redirect(url_for('patients_list'))
    return render_template('patients/add_patient.html')


@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    """Отображает форму для добавления сотрудника и обрабатывает ее."""
    if request.method == 'POST':
        fio = request.form['fio']
        position = request.form['position']
        phone = request.form['phone']
        specialization = request.form['specialization']
        query = "INSERT INTO Employees (FIO, Position, PhoneNumber, Specialization) VALUES (?, ?, ?, ?)"
        execute_query(query, (fio, position, phone, specialization), commit=True)
        return redirect(url_for('employees_list'))
    return render_template('employees/add_employee.html')


@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    """Отображает форму для добавления услуги и обрабатывает ее."""
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        cost = request.form['cost']
        description = request.form['description']
        detailed_description = request.form['detailed_description']
        query = "INSERT INTO Services (Name, Code, Cost, Description, DetailedDescription) VALUES (?, ?, ?, ?, ?)"
        execute_query(query, (name, code, cost, description, detailed_description), commit=True)
        return redirect(url_for('services_list'))
    return render_template('services/add_service.html')


@app.route('/add_appointment', methods=['GET', 'POST'])
def add_appointment():
    """Отображает форму для добавления приема и обрабатывает ее."""
    employees = get_employees_from_db()
    patients = get_patients_from_db()
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        doctor = request.form['doctor']
        patient = request.form['patient']
        complaints = request.form['complaints']
        preliminary_diagnosis = request.form['preliminary_diagnosis']
        query = "INSERT INTO Appointments (id_doctor, id_patient, Date, Time, Complaints, PreliminaryDiagnosis) VALUES (?, ?, ?, ?, ?, ?)"
        execute_query(query, (doctor, patient, date, time, complaints, preliminary_diagnosis), commit=True)
        return redirect(url_for('appointments_list'))
    return render_template('appointments/add_appointment.html', employees=employees, patients=patients)


@app.route('/add_payment', methods=['GET', 'POST'])
def add_payment():
    """Отображает форму для добавления платежа и обрабатывает ее."""
    services = get_services_from_db()
    patients = get_patients_from_db()
    employees = get_employees_from_db()
    if request.method == 'POST':
        date = request.form['date']
        payment_time = request.form['time']
        patient = request.form['patient']
        service = request.form['service']
        summ = request.form['summ']
        employee = request.form['employee']
        query = "INSERT INTO Payments (id_patient, id_service, Date, Summ, payment_time, employee_id) VALUES (?, ?, ?, ?, ?, ?)"
        execute_query(query, (patient, service, date, summ, payment_time, employee), commit=True)
        return redirect(url_for('payments_list'))
    return render_template('payments/add_payment.html', services=services, patients=patients, employees=employees)


@app.route('/generate_payment_check/<int:payment_id>')
def generate_payment_check_page(payment_id):
    """Генерирует и отправляет чек об оплате."""
    payment_data = get_payment_from_db(payment_id)
    clinic_info = get_clinic_info()
    if not payment_data:
        return render_template('404.html'), 404
    output_path = generate_payment_check(payment_data, clinic_info)
    return send_file(output_path, as_attachment=True, download_name=f'payment_{payment_id}_cheque.docx')

@app.route('/generate_workload_report', methods=['GET', 'POST'])
def generate_workload_report_page():
    """Генерирует и отправляет отчет о загрузке персонала."""
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        employee_id = request.form.get('employee_id', None)
        if not start_date or not end_date:
            return render_template('error_report.html', error='Необходимо ввести даты!')
        try:
            output_path = generate_workload_report(start_date, end_date, employee_id)
            return send_file(output_path, as_attachment=True, download_name='workload_report.xlsx')
        except Exception as e:
            return render_template('error_report.html', error='Ошибка при генерации отчета!')
    employees = get_employees_from_db()
    return render_template('reports/workload_report_form.html', employees=employees)

@app.errorhandler(404)
def page_not_found(error):
    """Обработчик ошибки 404."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)