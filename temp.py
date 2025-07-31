from app import app, db
from models import QuarteiraoConquistado

def resetar_quarteiroes():
    with app.app_context():
        db.session.execute(db.delete(QuarteiraoConquistado))
        db.session.commit()
        print("🔥 Quarteirões conquistados removidos do banco dominios.db!")

if __name__ == "__main__":
    resetar_quarteiroes()
