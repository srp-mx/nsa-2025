"""
Views for the app.

This file contains the view functions that handle requests and responses
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Organization, Auditor, Audit, Measurement


def home(request):
    return HttpResponse(":D")


# Utility: parse request body safely
def parse_body(request):
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}
    return {}


# ---------------- ORGANIZATION ----------------
@csrf_exempt
def organization_list(request):
    if request.method == "GET":
        data = list(Organization.objects.values("id", "user_id"))
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        user = get_object_or_404(User, id=body.get("user_id"))
        org = Organization.objects.create(user=user)
        return JsonResponse({"id": org.id, "user_id": org.user.id})


@csrf_exempt
def organization_detail(request, pk):
    org = get_object_or_404(Organization, pk=pk)

    if request.method == "GET":
        return JsonResponse({"id": org.id, "user_id": org.user.id})

    elif request.method == "POST":  # update
        body = parse_body(request)
        if "user_id" in body:
            org.user = get_object_or_404(User, id=body["user_id"])
        org.save()
        return JsonResponse({"id": org.id, "user_id": org.user.id})

    elif request.method == "DELETE":
        org.delete()
        return JsonResponse({"deleted": True})


# ---------------- AUDITOR ----------------
@csrf_exempt
def auditor_list(request):
    if request.method == "GET":
        data = list(Auditor.objects.values("id", "user_id"))
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        user = get_object_or_404(User, id=body.get("user_id"))
        auditor = Auditor.objects.create(user=user)
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})


@csrf_exempt
def auditor_detail(request, pk):
    auditor = get_object_or_404(Auditor, pk=pk)

    if request.method == "GET":
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})

    elif request.method == "POST":  # update
        body = parse_body(request)
        if "user_id" in body:
            auditor.user = get_object_or_404(User, id=body["user_id"])
        auditor.save()
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})

    elif request.method == "DELETE":
        auditor.delete()
        return JsonResponse({"deleted": True})


# ---------------- AUDIT ----------------
@csrf_exempt
def audit_list(request):
    if request.method == "GET":
        data = list(Audit.objects.values())
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        audit = Audit.objects.create(
            score=body.get("score"),
            max_score=body.get("max_score"),
            is_passing=body.get("is_passing", False),
            notes=body.get("notes", ""),
            organization_id=body.get("organization_id"),
            auditor_id=body.get("auditor_id"),
        )
        return JsonResponse({"id": audit.id})


@csrf_exempt
def audit_detail(request, pk):
    audit = get_object_or_404(Audit, pk=pk)

    if request.method == "GET":
        return JsonResponse({
            "id": audit.id,
            "score": audit.score,
            "max_score": audit.max_score,
            "is_passing": audit.is_passing,
            "notes": audit.notes,
            "organization_id": audit.organization_id,
            "auditor_id": audit.auditor_id,
        })

    elif request.method == "POST":  # update
        body = parse_body(request)
        for field in ["score", "max_score", "is_passing", "notes", "organization_id", "auditor_id"]:
            if field in body:
                setattr(audit, field, body[field])
        audit.save()
        return JsonResponse({"updated": True})

    elif request.method == "DELETE":
        audit.delete()
        return JsonResponse({"deleted": True})


# ---------------- MEASUREMENT ----------------
@csrf_exempt
def measurement_list(request):
    if request.method == "GET":
        data = list(Measurement.objects.values())
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        measurement = Measurement.objects.create(
            start_time=body.get("start_time"),
            end_time=body.get("end_time"),
            region=body.get("region"),  # NOTE: must be a valid GeoJSON or WKT string
            organization_id=body.get("organization_id"),
        )
        return JsonResponse({"id": measurement.id})


@csrf_exempt
def measurement_detail(request, pk):
    measurement = get_object_or_404(Measurement, pk=pk)

    if request.method == "GET":
        return JsonResponse({
            "id": measurement.id,
            "start_time": measurement.start_time,
            "end_time": measurement.end_time,
            "region": measurement.region.geojson if measurement.region else None,
            "organization_id": measurement.organization_id,
        })

    elif request.method == "POST":  # update
        body = parse_body(request)
        for field in ["start_time", "end_time", "region", "organization_id"]:
            if field in body:
                setattr(measurement, field, body[field])
        measurement.save()
        return JsonResponse({"updated": True})

    elif request.method == "DELETE":
        measurement.delete()
        return JsonResponse({"deleted": True})

