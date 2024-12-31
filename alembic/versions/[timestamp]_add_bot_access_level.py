"""add_bot_access_level

Revision ID: [generated_id]
Revises: [previous_revision]
Create Date: [timestamp]

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '[generated_id]'
down_revision = '[previous_revision]'
branch_labels = None
depends_on = None

def upgrade():
    # Create AccessLevelEnum type
    op.execute("CREATE TYPE accesslevelenum AS ENUM ('ORG_LEVEL', 'TEAM_LEVEL', 'HYBRID')")
    
    # Add access_level column to bots table
    op.add_column('bots',
        sa.Column('access_level', 
                  postgresql.ENUM('ORG_LEVEL', 'TEAM_LEVEL', 'HYBRID', name='accesslevelenum'),
                  nullable=False,
                  server_default='ORG_LEVEL')
    )

    # Create team_bot_access table
    op.create_table('team_bot_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'bot_id', name='unique_team_bot')
    )

def downgrade():
    op.drop_table('team_bot_access')
    op.drop_column('bots', 'access_level')
    op.execute("DROP TYPE accesslevelenum") 