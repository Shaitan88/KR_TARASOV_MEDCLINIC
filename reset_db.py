import sqlite3


def reset_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Удаление таблиц (если они есть)
    cursor.execute("DROP TABLE IF EXISTS Patients;")
    cursor.execute("DROP TABLE IF EXISTS Employees;")
    cursor.execute("DROP TABLE IF EXISTS Services;")
    cursor.execute("DROP TABLE IF EXISTS Appointments;")
    cursor.execute("DROP TABLE IF EXISTS Payments;")
    cursor.execute("DROP TABLE IF EXISTS ClinicInfo;")

    # Создание таблиц
    cursor.execute('''
        CREATE TABLE Patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            FIO TEXT NOT NULL,
            DateOfBirth DATE,
            PhoneNumber TEXT,
            Address TEXT,
            InsurancePolicy TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE Employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            FIO TEXT NOT NULL,
            Position TEXT NOT NULL,
            PhoneNumber TEXT,
            Specialization TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE Services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Code TEXT UNIQUE,
            Cost REAL NOT NULL,
            Description TEXT,
            DetailedDescription TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE Appointments (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_doctor INTEGER NOT NULL,
            id_patient INTEGER NOT NULL,
            Date DATE NOT NULL,
            Time TIME NOT NULL,
            Complaints TEXT,
            PreliminaryDiagnosis TEXT,
            FOREIGN KEY (id_doctor) REFERENCES Employees(id),
            FOREIGN KEY (id_patient) REFERENCES Patients(id)
        );
    ''')

    cursor.execute('''
        CREATE TABLE Payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_patient INTEGER NOT NULL,
            id_service INTEGER NOT NULL,
            Date DATE NOT NULL,
            Summ REAL NOT NULL,
            payment_time TEXT,
            employee_id INTEGER,
            FOREIGN KEY (id_patient) REFERENCES Patients(id),
            FOREIGN KEY (id_service) REFERENCES Services(id),
             FOREIGN KEY (employee_id) REFERENCES Employees(id)
         );
    ''')
    cursor.execute('''
    CREATE TABLE ClinicInfo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Address TEXT NOT NULL,
        PhoneNumber TEXT NOT NULL
    );
    ''')

    # Добавление начальных данных
    cursor.execute(
        "INSERT INTO Patients (FIO, DateOfBirth, PhoneNumber, Address, InsurancePolicy) VALUES (?, ?, ?, ?, ?)",
        ("Иванов Иван Иванович", "1980-01-15", "+79123456789", "ул. Пушкина, д. 1", "1234567890123456"))
    cursor.execute(
        "INSERT INTO Patients (FIO, DateOfBirth, PhoneNumber, Address, InsurancePolicy) VALUES (?, ?, ?, ?, ?)",
        ("Петров Петр Петрович", "1990-05-20", "+79129876543", "ул. Ленина, д. 10", "6543210987654321"))
    cursor.execute(
        "INSERT INTO Patients (FIO, DateOfBirth, PhoneNumber, Address, InsurancePolicy) VALUES (?, ?, ?, ?, ?)",
        ("Сидорова Анна Сергеевна", "1995-10-10", "+79121234567", "ул. Гагарина, д. 5", "1122334455667788"))

    cursor.execute("INSERT INTO Employees (FIO, Position, PhoneNumber, Specialization) VALUES (?, ?, ?, ?)",
                   ("Петрова Елена Сергеевна", "Терапевт", "+79234567890", "Общая практика"))
    cursor.execute("INSERT INTO Employees (FIO, Position, PhoneNumber, Specialization) VALUES (?, ?, ?, ?)",
                   ("Иванов Алексей Иванович", "Медсестра", "+79239876543", "Процедурный кабинет"))
    cursor.execute("INSERT INTO Employees (FIO, Position, PhoneNumber, Specialization) VALUES (?, ?, ?, ?)",
                   ("Смирнова Ольга Петровна", "Администратор", "+79231234567", "Регистратура"))

    cursor.execute("INSERT INTO Services (Name, Code, Cost, Description, DetailedDescription) VALUES (?, ?, ?, ?, ?)",
                   ("Консультация терапевта", "CONS", 1500, "Первичный осмотр",
                    "Подробная консультация, включая сбор анамнеза, осмотр и постановку предварительного диагноза."))
    cursor.execute("INSERT INTO Services (Name, Code, Cost, Description, DetailedDescription) VALUES (?, ?, ?, ?, ?)",
                   ("Анализ крови", "LAB-001", 1000, "Общий анализ",
                    "Включает в себя подсчет форменных элементов крови, определение гематокрита, СОЭ и лейкоцитарной формулы."))
    cursor.execute("INSERT INTO Services (Name, Code, Cost, Description, DetailedDescription) VALUES (?, ?, ?, ?, ?)",
                   ("ЭКГ", "ECG-001", 2000, "Электрокардиография",
                    "Процедура для определения электрической активности сердца с помощью электродов."))

    cursor.execute(
        "INSERT INTO Appointments (id_doctor, id_patient, Date, Time, Complaints, PreliminaryDiagnosis) VALUES (?, ?, ?, ?, ?, ?)",
        (1, 1, "2024-02-28", "10:00", "головная боль", "ОРВИ?"))
    cursor.execute(
        "INSERT INTO Appointments (id_doctor, id_patient, Date, Time, Complaints, PreliminaryDiagnosis) VALUES (?, ?, ?, ?, ?, ?)",
        (2, 2, "2024-02-29", "14:00", "слабость", "ОРЗ?"))
    cursor.execute(
        "INSERT INTO Appointments (id_doctor, id_patient, Date, Time, Complaints, PreliminaryDiagnosis) VALUES (?, ?, ?, ?, ?, ?)",
        (1, 3, "2024-03-01", "09:00", "кашель", "Бронхит?"))

    cursor.execute(
        "INSERT INTO Payments (id_patient, id_service, Date, Summ, payment_time, employee_id) VALUES (?, ?, ?, ?, ?, ?)",
        (1, 1, "2024-02-28", 1500, "10:00", 3))
    cursor.execute(
        "INSERT INTO Payments (id_patient, id_service, Date, Summ, payment_time, employee_id) VALUES (?, ?, ?, ?, ?, ?)",
        (2, 2, "2024-02-29", 1000, "14:00", 3))
    cursor.execute(
        "INSERT INTO Payments (id_patient, id_service, Date, Summ, payment_time, employee_id) VALUES (?, ?, ?, ?, ?, ?)",
        (3, 3, "2024-03-01", 2000, "09:00", 3))

    cursor.execute("INSERT INTO ClinicInfo (Name, Address, PhoneNumber) VALUES (?, ?, ?)",
                   ("Медицинская клиника", "ул. Примерная, д. 1", "+74951234567"))
    conn.commit()
    conn.close()
    print("Database reset successfully.")


if __name__ == '__main__':
    db_file = 'medclinic.db'  # Имя вашей базы данных
    reset_database(db_file)