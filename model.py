class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mssv = db.Column(db.String(50))
    content = db.Column(db.Text, nullable=False)