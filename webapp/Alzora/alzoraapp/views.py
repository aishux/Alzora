from django.shortcuts import render
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import auth
from django.contrib import messages
from .models import *
from google.cloud import bigquery


bigquery_client = bigquery.Client()


def handleLogin(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        username = email.split("@")[0]
        user = authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            
            if request.user.is_authenticated:
                messages.success(request, 'Logged in Successfully!')
                return HttpResponseRedirect(reverse("mainpage"))
        
        messages.error(request, 'Authentication Failed! Please check credentials')
    return render(request, "login.html")


def handleSignup(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname")
        email = request.POST.get("email")
        password = request.POST.get("password")
        username = email.split("@")[0]
        fullname = fullname.split()
        user = CustomUser.objects.create_user(username=username, email=email, password=password, user_type="caretaker")

        user.first_name = fullname[0]
        if len(fullname) > 1:
            user.last_name = fullname[1]
        else:
            user.last_name = ""

        caretaker = Caretakers(
            caretaker_id=user.id,
            full_name=user.first_name + " " + user.last_name,
            email=email
        )

        caretaker.save()

        messages.success(request, "Successfully Signed Up! Please login now")

    return HttpResponseRedirect(reverse("login"))


def handleLogout(request):
    if request.user.is_authenticated:
        auth.logout(request)
        messages.success(request, "Successfully Logged out!")
    return HttpResponseRedirect(reverse("mainpage"))


def mainpage(request):
    return render(request, "index.html")


def addPatient(request):
    if request.method == "POST":
        patient_username = request.POST.get("patient_username")
        patient_password = request.POST.get("patient_password")
        patient_first_name = request.POST.get("patient_first_name")
        patient_last_name = request.POST.get("patient_last_name")
        patient_age = request.POST.get("patient_age")
        patient_gender = request.POST.get("patient_gender")
        safe_center_lat = request.POST.get("safe_center_lat")
        safe_center_long = request.POST.get("safe_center_long")
        safe_radius_meters = request.POST.get("safe_radius_meters")

        user = CustomUser.objects.create_user(username=patient_username, password=patient_password, user_type="patient")
        user.first_name = patient_first_name
        user.last_name = patient_last_name

        patient = Patients(
            patient_id=user.id,
            first_name=patient_first_name,
            last_name=patient_last_name,
            age=patient_age,
            gender=patient_gender,
            safe_center_lat=safe_center_lat,
            safe_center_long=safe_center_long,
            safe_radius_meters=safe_radius_meters,
        )

        patient.save()

        caretaker = Caretakers.objects.filter(caretaker_id=request.user.id).first()

        caretaker.patient_ids += [patient.patient_id]

        caretaker.save()

    elif request.user.is_authenticated and request.user.user_type == "caretaker":
        caretaker = Caretakers.objects.filter(caretaker_id=request.user.id).first()
        patient_ids = caretaker.patient_ids
        all_patients = Patients.objects.filter(patient_id__in=patient_ids)

        return render(request, "add-patient.html", {"all_patients":all_patients})
    
    elif request.user.is_authenticated and request.user.user_type == "patient":
        messages.error(request, "You are not authorized for this page!")
        return HttpResponseRedirect(reverse("mainpage"))

    else:
        return HttpResponseRedirect(reverse("login"))


def chat(request):
    if request.user.is_authenticated and request.user.user_type == "caretaker":
        caretaker = Caretakers.objects.filter(caretaker_id=request.user.id).first()
        patient_ids = caretaker.patient_ids
        all_patients = Patients.objects.filter(patient_id__in=patient_ids)
        if all_patients:
            return render(request, "chat.html", {"all_patients": all_patients})
        else:
            messages.error(request, "Please add atleast one patient first!")
            return HttpResponseRedirect(reverse("addPatient"))
    elif request.user.is_authenticated and request.user.user_type == "patient":
        return render(request, "chat.html", {"patient_id": request.user.id})
    else:
        return HttpResponseRedirect(reverse("login"))


def dashboard(request):
    if request.user.is_authenticated and request.user.user_type == "caretaker":
        caretaker = Caretakers.objects.filter(caretaker_id=request.user.id).first()
        patient_ids = caretaker.patient_ids
        all_patients = Patients.objects.filter(patient_id__in=patient_ids)
        if all_patients:
            return render(request, "dashboard.html", {"all_patients": all_patients})
        else:
            messages.error(request, "Please add atleast one patient first!")
            return HttpResponseRedirect(reverse("addPatient"))
    elif request.user.is_authenticated and request.user.user_type == "patient":
        return render(request, "dashboard.html")
    else:
        return HttpResponseRedirect(reverse("login"))


def patientInfo(request, patient_id):
    patient = Patients.objects.filter(patient_id=patient_id).first()
    data = {
        "patient_id": patient_id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "age": patient.age,
        "gender": patient.gender,
        "safe_center_lat": patient.safe_center_lat,
        "safe_center_long": patient.safe_center_long,
        "safe_radius_meters": patient.safe_radius_meters,
    }
    return JsonResponse(data)


def updatePatientInfo(request):
    if request.method == "POST":
        patient_id = request.POST.get("patient_id")
        
        patient = Patients.objects.filter(patient_id=patient_id).first()
        caretaker = Caretakers.objects.filter(caretaker_id=request.user.id).first()
        patient_ids = caretaker.patient_ids
        if patient_id not in patient_ids:
            messages.error(request, "Sorry you're not the caretaker of this patient!")
            return HttpResponseRedirect(reverse("addPatient"))
        
        edited_first_name = request.POST.get("editFirstName")
        edited_last_name = request.POST.get("editLastName")
        edited_age = request.POST.get("editAge")
        edited_gender = request.POST.get("editGender")
        edited_safe_center_lat = request.POST.get("editSafeLt")
        edited_safe_center_long = request.POST.get("editSafeLong")
        edited_safe_radius_meters = request.POST.get("editSafeRad")

        patient.first_name=edited_first_name,
        patient.last_name=edited_last_name,
        patient.age=edited_age,
        patient.gender=edited_gender,
        patient.safe_center_lat=edited_safe_center_lat,
        patient.safe_center_long=edited_safe_center_long,
        patient.safe_radius_meters=edited_safe_radius_meters,

        # Save
        patient.save()

        messages.success(request, "Patient Data updated successfully!")

    return HttpResponseRedirect(reverse("addPatient"))


def chartData(request, patient_id):

    query_job = bigquery_client.query(f'''
        SELECT
            DATE(`timestamp`) AS `day`,
            ROUND(AVG(`value_heart_rate`),2) AS `avg_heart_rate`,
            ROUND(AVG(`value_step_count`),2) AS `avg_step_count`,
            ROUND(AVG(`value_sp_o_2`),2) AS `avg_spO2_level`,
            ROUND(SUM(CAST(value_fall_flag AS INT64)), 2) AS total_fall_flag
        FROM
            `patients_vitals.patient_vitals`
        WHERE
            `value_patient_id` = {patient_id}
        GROUP BY
            `day`
        ORDER BY
            `day`
        LIMIT 7
    ''')
    data_collection = query_job.result()

    data_collection = data_collection.to_dataframe()
    data_collection = data_collection.sort_values("day")

    # Labels = days
    labels = data_collection["day"]

    heart_rate = data_collection["avg_heart_rate"]
    spO2_level = data_collection["avg_spO2_level"]
    step_count = data_collection["avg_step_count"]
    fall_events = data_collection["total_fall_flag"]

    data = {
        "labels": labels,

        "bar_heart_rate": {
            "labels": labels,
            "datasets": [{"label": "Avg Heart Rate", "data": heart_rate, "backgroundColor": "#4b6eb8"}],
        },

        "bar_spo2_level": {
            "labels": labels,
            "datasets": [{"label": "Average SpO2 levels", "data": spO2_level, "backgroundColor": "#4b6eb8"}]
        },

        "step_count": {
            "labels": labels,
            "datasets": [{"label": "Step Count", "data": step_count}]
        },

        "radar_comparison": {
            "labels": ["Heart Rate", "SpO2 Levels", "Step Count", "Fall Events"],
            "datasets": [{
                "label": "Weekly Avg",
                "data": [
                    sum(heart_rate) / len(heart_rate) if heart_rate else 0,
                    sum(spO2_level) / len(spO2_level) if spO2_level else 0,
                    sum(step_count) / len(step_count) if step_count else 0,
                    sum(fall_events) / len(fall_events) if fall_events else 0
                ],
                "backgroundColor": "#477AEB", 
                "borderColor": "#2e5bbc"
            }]
        },

        "pie_distribution": {
            "labels": ["Heart Rate", "SpO2 Levels", "Step Count", "Fall Events"],
            "datasets": [{
                "data": [
                    sum(heart_rate),
                    sum(spO2_level),
                    sum(step_count)
                ],
                "backgroundColor": ["#4b6eb8", "#7B98D7", "#E2EBFE"]
            }]
        },

        "bubble_chart": {
            "datasets": [{
                "label": "SpO2 Levels vs Miles vs HR",
                "data": [
                    {"x": m, "y": s, "r": (c / step_count) * 20}  # max bubble = 20px
                    for m, s, c in zip(step_count, spO2_level, heart_rate)
                ],
                "backgroundColor": '#4b6eb8',
            }]
        }
    }

    return JsonResponse(data)