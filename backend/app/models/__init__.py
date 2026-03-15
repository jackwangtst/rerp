"""所有模型统一在此导入，供 Alembic autogenerate 使用"""
from app.models.user import SysUser  # noqa: F401
from app.models.customer import Customer, Contact, CustomerFollowUp  # noqa: F401
from app.models.lead import Lead, LeadFollowUp  # noqa: F401
from app.models.opportunity import Opportunity, OpportunityFollowUp  # noqa: F401
from app.models.quotation import Quotation  # noqa: F401
from app.models.contract import Contract, ContractItem, PaymentPlan, PaymentRecord  # noqa: F401
from app.models.project import CertProject, ProjectTask  # noqa: F401
from app.models.price_catalog import PriceCatalog  # noqa: F401
from app.models.expense import Expense  # noqa: F401
from app.models.quotation_payment import QuotationPayment, QuotationPaymentRecord  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
