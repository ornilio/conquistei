"""Adiciona campo categoria em quarteiroes_conquistados"""

from alembic import op
import sqlalchemy as sa

# ID único da revisão — pode ser algo como 'abc12345categoria'
revision = 'add_categoria_coluna'
down_revision = None  # Ou o ID da última migração, se houver
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('quarteiroes_conquistados', sa.Column('categoria', sa.String(length=50)))

def downgrade():
    op.drop_column('quarteiroes_conquistados', 'categoria')
