"""
Test Factory to make fake objects for testing
"""

from datetime import date, timedelta
from decimal import Decimal
import factory
from factory.fuzzy import FuzzyChoice, FuzzyDate, FuzzyDecimal
from service.models import Promotion, PromotionType


class PromotionFactory(factory.Factory):
    """Creates fake promotions for testing"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Promotion

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("catch_phrase")
    promotion_type = FuzzyChoice(choices=list(PromotionType))
    value = factory.Maybe(
        factory.LazyAttribute(lambda o: o.promotion_type == PromotionType.BOGO),
        yes_declaration=Decimal("0"),
        no_declaration=FuzzyDecimal(1, 100, 2),
    )
    product_id = FuzzyChoice(choices=[None, 101, 202, 303, 404])
    start_date = FuzzyDate(date(2026, 1, 1), date(2026, 12, 31))
    end_date = factory.LazyAttribute(lambda o: o.start_date + timedelta(days=30))
    active = FuzzyChoice(choices=[True, False])
