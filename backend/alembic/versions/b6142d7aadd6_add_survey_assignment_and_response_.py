"""Add survey assignment and response tables

Revision ID: b6142d7aadd6
Revises: 0a85327f9d31
Create Date: 2026-05-19 10:15:04.307795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6142d7aadd6'
down_revision: Union[str, Sequence[str], None] = '0a85327f9d31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands adjusted: only create new survey tables and add missing columns ###
    # (Existing core tables already present in DB - skip creating them)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'survey_assignments' not in inspector.get_table_names():
        op.create_table('survey_assignments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('survey_template_id', sa.Integer(), nullable=False),
    sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
    sa.Column('assigned_to_department_id', sa.Integer(), nullable=True),
    sa.Column('assigned_to_organization_id', sa.Integer(), nullable=True),
    sa.Column('assigned_by', sa.Integer(), nullable=False),
    sa.Column('assignment_status', sa.String(), nullable=True),
    sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['assigned_to_department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['assigned_to_organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['survey_template_id'], ['survey_templates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
        existing_idx = {i['name'] for i in inspector.get_indexes('survey_assignments')}
        if 'ix_survey_assignments_assigned_at' not in existing_idx:
            op.create_index(op.f('ix_survey_assignments_assigned_at'), 'survey_assignments', ['assigned_at'], unique=False)
        if 'ix_survey_assignments_assigned_by' not in existing_idx:
            op.create_index(op.f('ix_survey_assignments_assigned_by'), 'survey_assignments', ['assigned_by'], unique=False)
        if 'ix_survey_assignments_assigned_to_department_id' not in existing_idx:
            op.create_index(op.f('ix_survey_assignments_assigned_to_department_id'), 'survey_assignments', ['assigned_to_department_id'], unique=False)
        if 'ix_survey_assignments_assigned_to_organization_id' not in existing_idx:
            op.create_index(op.f('ix_survey_assignments_assigned_to_organization_id'), 'survey_assignments', ['assigned_to_organization_id'], unique=False)
        if 'ix_survey_assignments_assigned_to_user_id' not in existing_idx:
            op.create_index(op.f('ix_survey_assignments_assigned_to_user_id'), 'survey_assignments', ['assigned_to_user_id'], unique=False)
        if 'ix_survey_assignments_assignment_status' not in existing_idx:
            op.create_index(op.f('ix_survey_assignments_assignment_status'), 'survey_assignments', ['assignment_status'], unique=False)
        if 'ix_survey_assignments_id' not in existing_idx:
            op.create_index(op.f('ix_survey_assignments_id'), 'survey_assignments', ['id'], unique=False)
        if 'ix_survey_assignments_survey_template_id' not in existing_idx:
            op.create_index(op.f('ix_survey_assignments_survey_template_id'), 'survey_assignments', ['survey_template_id'], unique=False)
    if 'survey_responses' not in inspector.get_table_names():
        op.create_table('survey_responses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('survey_template_id', sa.Integer(), nullable=False),
    sa.Column('respondent_user_id', sa.Integer(), nullable=False),
    sa.Column('survey_assignment_id', sa.Integer(), nullable=True),
    sa.Column('responses', sa.Text(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('ip_address', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['respondent_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['survey_assignment_id'], ['survey_assignments.id'], ),
    sa.ForeignKeyConstraint(['survey_template_id'], ['survey_templates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
        resp_idx = {i['name'] for i in inspector.get_indexes('survey_responses')}
        if 'ix_survey_responses_id' not in resp_idx:
            op.create_index(op.f('ix_survey_responses_id'), 'survey_responses', ['id'], unique=False)
        if 'ix_survey_responses_respondent_user_id' not in resp_idx:
            op.create_index(op.f('ix_survey_responses_respondent_user_id'), 'survey_responses', ['respondent_user_id'], unique=False)
        if 'ix_survey_responses_status' not in resp_idx:
            op.create_index(op.f('ix_survey_responses_status'), 'survey_responses', ['status'], unique=False)
        if 'ix_survey_responses_submitted_at' not in resp_idx:
            op.create_index(op.f('ix_survey_responses_submitted_at'), 'survey_responses', ['submitted_at'], unique=False)
        if 'ix_survey_responses_survey_assignment_id' not in resp_idx:
            op.create_index(op.f('ix_survey_responses_survey_assignment_id'), 'survey_responses', ['survey_assignment_id'], unique=False)
        if 'ix_survey_responses_survey_template_id' not in resp_idx:
            op.create_index(op.f('ix_survey_responses_survey_template_id'), 'survey_responses', ['survey_template_id'], unique=False)
    # Add columns to feedback if missing
    feedback_cols = [c['name'] for c in inspector.get_columns('feedback')]
    if 'department_tag' not in feedback_cols:
        op.add_column('feedback', sa.Column('department_tag', sa.String(), nullable=True))
        op.create_index(op.f('ix_feedback_department_tag'), 'feedback', ['department_tag'], unique=False)
    if 'routing_status' not in feedback_cols:
        op.add_column('feedback', sa.Column('routing_status', sa.String(), nullable=True))
        op.create_index(op.f('ix_feedback_routing_status'), 'feedback', ['routing_status'], unique=False)
    if 'routing_confidence' not in feedback_cols:
        op.add_column('feedback', sa.Column('routing_confidence', sa.Float(), nullable=True))

    # Add organization/department columns to users if missing
    user_cols = [c['name'] for c in inspector.get_columns('users')]
    if 'organization_id' not in user_cols:
        op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
        op.create_foreign_key(None, 'users', 'organizations', ['organization_id'], ['id'])
    if 'department_id' not in user_cols:
        op.add_column('users', sa.Column('department_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_users_department_id'), 'users', ['department_id'], unique=False)
        op.create_foreign_key(None, 'users', 'departments', ['department_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_index(op.f('ix_users_department_id'), table_name='users')
    op.drop_column('users', 'department_id')
    op.drop_column('users', 'organization_id')
    op.drop_index(op.f('ix_feedback_routing_status'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_department_tag'), table_name='feedback')
    op.drop_column('feedback', 'routing_confidence')
    op.drop_column('feedback', 'routing_status')
    op.drop_column('feedback', 'department_tag')
    op.drop_index(op.f('ix_survey_responses_survey_template_id'), table_name='survey_responses')
    op.drop_index(op.f('ix_survey_responses_survey_assignment_id'), table_name='survey_responses')
    op.drop_index(op.f('ix_survey_responses_submitted_at'), table_name='survey_responses')
    op.drop_index(op.f('ix_survey_responses_status'), table_name='survey_responses')
    op.drop_index(op.f('ix_survey_responses_respondent_user_id'), table_name='survey_responses')
    op.drop_index(op.f('ix_survey_responses_id'), table_name='survey_responses')
    op.drop_table('survey_responses')
    op.drop_index(op.f('ix_survey_assignments_survey_template_id'), table_name='survey_assignments')
    op.drop_index(op.f('ix_survey_assignments_id'), table_name='survey_assignments')
    op.drop_index(op.f('ix_survey_assignments_assignment_status'), table_name='survey_assignments')
    op.drop_index(op.f('ix_survey_assignments_assigned_to_user_id'), table_name='survey_assignments')
    op.drop_index(op.f('ix_survey_assignments_assigned_to_organization_id'), table_name='survey_assignments')
    op.drop_index(op.f('ix_survey_assignments_assigned_to_department_id'), table_name='survey_assignments')
    op.drop_index(op.f('ix_survey_assignments_assigned_by'), table_name='survey_assignments')
    op.drop_index(op.f('ix_survey_assignments_assigned_at'), table_name='survey_assignments')
    op.drop_table('survey_assignments')
    op.drop_index(op.f('ix_user_settings_user_id'), table_name='user_settings')
    op.drop_index(op.f('ix_user_settings_id'), table_name='user_settings')
    op.drop_table('user_settings')
    op.drop_index(op.f('ix_survey_templates_id'), table_name='survey_templates')
    op.drop_index(op.f('ix_survey_templates_created_by'), table_name='survey_templates')
    op.drop_table('survey_templates')
    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_buyer_departments_id'), table_name='buyer_departments')
    op.drop_index(op.f('ix_buyer_departments_department_id'), table_name='buyer_departments')
    op.drop_index(op.f('ix_buyer_departments_buyer_id'), table_name='buyer_departments')
    op.drop_table('buyer_departments')
    op.drop_index(op.f('ix_departments_organization_id'), table_name='departments')
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    op.drop_table('departments')
    op.drop_index(op.f('ix_buyers_organization_id'), table_name='buyers')
    op.drop_index(op.f('ix_buyers_id'), table_name='buyers')
    op.drop_table('buyers')
    op.drop_index(op.f('ix_role_permissions_role'), table_name='role_permissions')
    op.drop_index(op.f('ix_role_permissions_permission'), table_name='role_permissions')
    op.drop_index(op.f('ix_role_permissions_id'), table_name='role_permissions')
    op.drop_table('role_permissions')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
    # ### end Alembic commands ###
