import datetime as dt
import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

# ──────────────────────── MODELS ────────────────────────

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    user_code = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    phone = db.Column(db.String(20))
    parent_phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    position = db.Column(db.String(100))
    password_hash = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    avatar = db.Column(db.String(100), default="default.jpg")
    salary_rate_per_hour = db.Column(db.Integer, default=0)
    linked_student_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    linked_student = db.relationship("User", remote_side=[id], uselist=False)
    courses_taught = db.relationship("Course", back_populates="teacher", foreign_keys="Course.teacher_id")
    schedules = db.relationship("Schedule", back_populates="teacher", foreign_keys="Schedule.teacher_id")
    enrollments = db.relationship("Enrollment", back_populates="student", foreign_keys="Enrollment.student_id")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash or "", password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_manager(self):
        return self.role == "manager"


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(80), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    classroom = db.Column(db.String(40))
    description = db.Column(db.Text)
    tuition_amount = db.Column(db.Integer, default=0)
    tuition_type = db.Column(db.String(20), default="monthly")
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

    teacher = db.relationship("User", back_populates="courses_taught", foreign_keys=[teacher_id])
    schedules = db.relationship("Schedule", back_populates="course", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    tuition_payments = db.relationship("TuitionPayment", back_populates="course", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    classroom = db.Column(db.String(40), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)

    course = db.relationship("Course", back_populates="schedules")
    teacher = db.relationship("User", back_populates="schedules", foreign_keys=[teacher_id])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    status = db.Column(db.String(20), default="active")
    enrolled_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    student = db.relationship("User", back_populates="enrollments", foreign_keys=[student_id])
    course = db.relationship("Course", back_populates="enrollments")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="uq_student_course"),)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=dt.date.today)
    status = db.Column(db.String(20), nullable=False, default="present")
    note = db.Column(db.Text)
    marked_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    student = db.relationship("User", foreign_keys=[student_id])
    course = db.relationship("Course")
    marked_by = db.relationship("User", foreign_keys=[marked_by_id])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    __table_args__ = (db.UniqueConstraint("student_id", "course_id", "date", name="uq_attendance_student_course_date"),)


class TeacherPayroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)
    total_classes = db.Column(db.Integer, default=0)
    total_hours = db.Column(db.Float, default=0)
    salary_amount = db.Column(db.Integer, default=0)
    calculated_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    teacher = db.relationship("User")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    __table_args__ = (db.UniqueConstraint("teacher_id", "month", name="uq_teacher_payroll_month"),)


class TeachingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    classroom = db.Column(db.String(40), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    hours_taught = db.Column(db.Float, nullable=False)
    hourly_rate = db.Column(db.Integer, nullable=False, default=0)
    amount_earned = db.Column(db.Integer, nullable=False, default=0)
    confirmed_by_teacher = db.Column(db.Boolean, default=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    teacher = db.relationship("User", foreign_keys=[teacher_id])
    course = db.relationship("Course")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    __table_args__ = (db.UniqueConstraint("teacher_id", "course_id", "date", name="uq_teaching_record_session"),)


class TuitionPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False, default=0)
    payment_type = db.Column(db.String(20), nullable=False, default="monthly")
    payment_date = db.Column(db.Date, nullable=False, default=dt.date.today)
    status = db.Column(db.String(20), nullable=False, default="paid")
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    student = db.relationship("User", foreign_keys=[student_id])
    course = db.relationship("Course", back_populates="tuition_payments")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# ──────────────────────── EXAM MODELS ────────────────────────

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)
    shuffle_questions = db.Column(db.Boolean, default=True)
    shuffle_answers = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    course = db.relationship("Course")
    creator = db.relationship("User", foreign_keys=[created_by])
    questions = db.relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan", order_by="ExamQuestion.order_index")
    submissions = db.relationship("ExamSubmission", back_populates="exam", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def total_points(self):
        return sum(q.points for q in self.questions)

    @property
    def question_count(self):
        return len(self.questions)

    @property
    def status_label(self):
        now = dt.datetime.utcnow()
        if not self.is_active:
            return "closed"
        if self.start_time and now < self.start_time:
            return "upcoming"
        if self.end_time and now > self.end_time:
            return "closed"
        return "open"


class ExamQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False, default="single")  # single, multi, truefalse
    points = db.Column(db.Float, default=1.0)
    order_index = db.Column(db.Integer, default=0)

    exam = db.relationship("Exam", back_populates="questions")
    answers = db.relationship("ExamAnswer", back_populates="question", cascade="all, delete-orphan", order_by="ExamAnswer.id")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ExamAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("exam_question.id"), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    question = db.relationship("ExamQuestion", back_populates="answers")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ExamSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    total_score = db.Column(db.Float, default=0)
    max_score = db.Column(db.Float, default=0)
    is_graded = db.Column(db.Boolean, default=False)

    exam = db.relationship("Exam", back_populates="submissions")
    student = db.relationship("User", foreign_keys=[student_id])
    answers = db.relationship("SubmissionAnswer", back_populates="submission", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def percentage(self):
        if self.max_score == 0:
            return 0
        return round(self.total_score / self.max_score * 100, 1)

    __table_args__ = (db.UniqueConstraint("exam_id", "student_id", name="uq_exam_student"),)


class SubmissionAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("exam_submission.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("exam_question.id"), nullable=False)
    selected_answer_ids = db.Column(db.Text, default="[]")  # JSON array of answer IDs
    is_correct = db.Column(db.Boolean, default=False)
    points_earned = db.Column(db.Float, default=0)

    submission = db.relationship("ExamSubmission", back_populates="answers")
    question = db.relationship("ExamQuestion")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_selected_ids(self):
        try:
            return json.loads(self.selected_answer_ids or "[]")
        except (json.JSONDecodeError, TypeError):
            return []
