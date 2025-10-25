from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

# Form
from .forms import NumbersForm

# Environment and MongoDB
import os
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

# Load .env if present (non-fatal if missing)
load_dotenv()


def _analyze_values(values: list[float]) -> dict:
    """
    Analyze values per assignment requirements and return a dict.
    - All numeric: ensured by form validation (True)
    - Negative warning: whether any negatives exist and which values
    - Average and > 50 evaluation
    - Positive count and parity (even/odd) via bitwise check
    - Values greater than 10, sorted ascending
    """
    # Original order preserved
    original = list(values)

    # Negative values
    negatives = [v for v in values if v < 0]
    has_negative = len(negatives) > 0

    # Average and threshold evaluation
    avg = sum(values) / len(values)
    avg_gt_50 = avg > 50

    # Positive count and parity (count & 1 == 0 means even)
    positive_count = sum(1 for v in values if v > 0)
    is_even = (positive_count & 1) == 0

    # Values strictly greater than 10, sorted
    greater_than_10_sorted = sorted([v for v in values if v > 10])

    return {
        "all_numeric": True,
        "original": original,
        "has_negative": has_negative,
        "negatives": negatives,
        "average": avg,
        "average_gt_50": avg_gt_50,
        "positive_count": positive_count,
        "positive_count_is_even": is_even,
        "gt10_sorted": greater_than_10_sorted,
    }


def _get_mongo_collection():
    """
    Helper to return a MongoDB collection handle.
    - Reads MONGO_URI, MONGO_DB, MONGO_COLLECTION from .env
    - Returns None if not configured or on failure (non-fatal)
    """
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        return None
    db_name = os.getenv("MONGO_DB", "assignment6")
    col_name = os.getenv("MONGO_COLLECTION", "submissions")
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        # Ping to verify connectivity (short timeout)
        _ = client.admin.command("ping")
        db = client[db_name]
        return db[col_name]
    except PyMongoError:
        return None


def index(request: HttpRequest) -> HttpResponse:
    """
    Home page.
    - GET: render input form
    - POST: validate, analyze, display results; save to MongoDB if configured
    """
    context: dict = {}

    if request.method == "POST":
        form = NumbersForm(request.POST)
        if form.is_valid():
            # Extract floats from cleaned_data
            a = form.cleaned_data["a"]
            b = form.cleaned_data["b"]
            c = form.cleaned_data["c"]
            d = form.cleaned_data["d"]
            e = form.cleaned_data["e"]
            values = [a, b, c, d, e]

            # Analyze
            result = _analyze_values(values)

            # Try saving to MongoDB (if configured)
            saved = False
            save_error: str | None = None
            col = _get_mongo_collection()
            if col is not None:
                try:
                    doc = {
                        "input": {
                            "a": a, "b": b, "c": c, "d": d, "e": e,
                        },
                        "result": result,
                        "created_at": datetime.utcnow(),
                    }
                    col.insert_one(doc)
                    saved = True
                except PyMongoError as ex:
                    save_error = f"Failed to save to MongoDB: {ex}"
            else:
                # Not configured; skip storing (non-fatal)
                save_error = "MongoDB is not configured (.env MONGO_URI is missing)"

            context.update({
                "form": form,
                "result": result,
                "saved": saved,
                "save_error": save_error,
            })
        else:
            # Validation errors (non-numeric etc.)
            context.update({
                "form": form,
                "result": None,
            })
    else:
        # Initial render
        context["form"] = NumbersForm()
        context["result"] = None

    return render(request, "bitwise/index.html", context)


def history(request: HttpRequest) -> HttpResponse:
    """
    History page: list recent submissions saved in MongoDB.
    If MongoDB is not configured or unreachable, display a helpful message.
    """
    col = _get_mongo_collection()
    entries: list[dict] = []
    error: str | None = None

    if col is None:
        error = "MongoDB is not configured or unreachable (.env MONGO_URI)"
    else:
        try:
            # Fetch latest 50 entries
            cursor = col.find({}).sort("created_at", -1).limit(50)
            entries = list(cursor)
        except PyMongoError as ex:
            error = f"Failed to fetch from MongoDB: {ex}"

    return render(request, "bitwise/history.html", {
        "entries": entries,
        "error": error,
    })
