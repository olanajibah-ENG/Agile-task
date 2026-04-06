from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# إعداد قاعدة البيانات SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'  # اسم الملف لقاعدة البيانات
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# نموذج المهمة (Task Model)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.Integer, default=1)
    assignedTo = db.Column(db.String(100), default="unknown")
    reminder_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'priority': self.priority,
            'assignedTo': self.assignedTo,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'is_completed': self.is_completed
        }

# إنشاء قاعدة البيانات إذا لم تكن موجودة
with app.app_context():
    db.create_all()

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint لعرض جميع المهام (GET /tasks)
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])

# Endpoint لإضافة مهمة جديدة (POST /tasks)
@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or not 'title' in data:
        return jsonify({'error': 'Title is required'}), 400
    
    priority = data.get('priority', 1)
    if not isinstance(priority, int) or priority < 1 or priority > 3:
        return jsonify({'error': 'Priority must be between 1 and 3'}), 400
    
    # Parse reminder_date if provided
    reminder_date = None
    if 'reminder_date' in data and data['reminder_date']:
        try:
            reminder_date = datetime.fromisoformat(data['reminder_date'])
        except ValueError:
            return jsonify({'error': 'Invalid reminder_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    new_task = Task(
        title=data['title'],
        description=data.get('description'),
        priority=priority,
        assignedTo=data.get('assignedTo') or "unknown",
        reminder_date=reminder_date,
        is_completed=data.get('is_completed', False)
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json()

    if 'priority' in data:
        priority = data['priority']
        if not isinstance(priority, int) or priority < 1 or priority > 3:
            return jsonify({'error': 'Priority must be between 1 and 3'}), 400

    # Parse reminder_date if provided
    if 'reminder_date' in data:
        if data['reminder_date'] is None:
            task.reminder_date = None
        else:
            try:
                task.reminder_date = datetime.fromisoformat(data['reminder_date'])
            except ValueError:
                return jsonify({'error': 'Invalid reminder_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.priority = data.get('priority', task.priority)
    task.assignedTo = data.get('assignedTo', task.assignedTo)
    task.is_completed = data.get('is_completed', task.is_completed)

    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'})

# Endpoint لتحديد المهمة كمكتملة (PATCH /tasks/<id>/complete)
@app.route('/tasks/<int:task_id>/complete', methods=['PATCH'])
def complete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    task.is_completed = True
    db.session.commit()
    return jsonify(task.to_dict())


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=9000)

