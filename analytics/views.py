"""
Analytics app views.

JSON endpoints for Chart.js dashboard visualizations.
"""

from calendar import month_name
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views import View

from accounts.views import StaffOnlyMixin
from wallet.models import Transaction, TransactionStatus


class SpendingByCategoryView(LoginRequiredMixin, StaffOnlyMixin, View):
    """
    JSON endpoint for spending by transaction category.

    Aggregates transaction sums by type (Deposit, Withdrawal, Transfer).
    Returns data formatted for Chart.js consumption.

    URL Parameters:
        - days: Number of days to look back (default: 30)

    Returns:
        JSON object with labels and data arrays for Chart.js
    """

    def get(self, request):
        """Return spending aggregated by transaction type."""
        # Get days parameter (default 30 days)
        days = int(request.GET.get("days", 30))

        # Calculate date range
        end_date = timezone.now()
        start_date = timezone.now() - timezone.timedelta(days=days)

        # Aggregate by transaction type
        categories = []
        data = []
        colors = []

        # Deposits
        deposits = Transaction.objects.filter(
            type="DEPOSIT",
            status=TransactionStatus.COMPLETED,
            created_at__gte=start_date,
            created_at__lte=end_date,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        categories.append("Deposits")
        data.append(float(deposits))
        colors.append("#606c38")  # Olive leaf (green)

        # Withdrawals
        withdrawals = Transaction.objects.filter(
            type="WITHDRAWAL",
            status=TransactionStatus.COMPLETED,
            created_at__gte=start_date,
            created_at__lte=end_date,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        categories.append("Withdrawals")
        data.append(float(withdrawals))
        colors.append("#c75d5d")  # Red

        # Transfers
        transfers = Transaction.objects.filter(
            type="TRANSFER",
            status=TransactionStatus.COMPLETED,
            created_at__gte=start_date,
            created_at__lte=end_date,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        categories.append("Transfers")
        data.append(float(transfers))
        colors.append("#bc6c25")  # Copperwood (orange)

        # Calculate total volume
        total_volume = deposits + withdrawals + transfers

        response_data = {
            "labels": categories,
            "datasets": [
                {
                    "label": f"Transaction Volume (Last {days} days)",
                    "data": data,
                    "backgroundColor": colors,
                    "borderColor": [color.replace("0.2", "1") for color in colors],
                    "borderWidth": 2,
                }
            ],
            "metadata": {
                "total_volume": float(total_volume),
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        }

        return JsonResponse(response_data)


class SpendingByMonthView(LoginRequiredMixin, StaffOnlyMixin, View):
    """
    JSON endpoint for spending by month.

    Aggregates transaction volume by month for the current year.
    Returns data formatted for Chart.js consumption.

    URL Parameters:
        - year: Year to query (default: current year)
        - type: Filter by transaction type (optional)

    Returns:
        JSON object with labels and data arrays for Chart.js
    """

    def get(self, request):
        """Return spending aggregated by month."""
        # Get year parameter (default: current year)
        year = int(request.GET.get("year", timezone.now().year))

        # Get optional type filter
        transaction_type = request.GET.get("type", None)

        # Build base queryset
        queryset = Transaction.objects.filter(
            status=TransactionStatus.COMPLETED,
            created_at__year=year,
        )

        # Apply type filter if provided
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)

        # Aggregate by month
        months_data = {}
        for month_num in range(1, 13):
            month_name_short = month_name[month_num][:3]
            months_data[month_num] = {
                "label": month_name_short,
                "volume": Decimal("0.00"),
            }

        # Get monthly aggregates (SQLite compatible)
        from django.db.models.functions import ExtractMonth

        monthly_totals = queryset.annotate(
            month=ExtractMonth("created_at")
        ).values("month").annotate(total=Sum("amount")).order_by("month")

        for item in monthly_totals:
            month_num = int(item["month"])
            if month_num in months_data:
                months_data[month_num]["volume"] = item["total"] or Decimal("0.00")

        # Prepare Chart.js data
        labels = [data["label"] for data in months_data.values()]
        data = [float(data["volume"]) for data in months_data.values()]

        # Calculate total and average
        total_volume = sum(months_data[month]["volume"] for month in months_data)
        months_with_data = sum(1 for month in months_data if months_data[month]["volume"] > 0)
        average = total_volume / months_with_data if months_with_data > 0 else Decimal("0.00")

        response_data = {
            "labels": labels,
            "datasets": [
                {
                    "label": f"Transaction Volume {year}" + (f" ({transaction_type})" if transaction_type else ""),
                    "data": data,
                    "backgroundColor": "rgba(188, 108, 37, 0.6)",  # Copperwood with transparency
                    "borderColor": "#bc6c25",
                    "borderWidth": 2,
                    "fill": True,
                    "tension": 0.4,  # Smooth curve for line chart
                }
            ],
            "metadata": {
                "year": year,
                "total_volume": float(total_volume),
                "average_monthly": float(average),
                "transaction_type": transaction_type or "ALL",
            },
        }

        return JsonResponse(response_data)
