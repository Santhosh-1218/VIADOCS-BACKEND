# backend/routes/admin_routes.py
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from bson import ObjectId

admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/dashboard", methods=["GET"])
def get_admin_dashboard():
    try:
        db = current_app.db
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500

        users_col = db["users"]
        docs_col = db["documents"]

        # --- Query Parameters ---
        referral_filter = request.args.get("referral", "overall").upper()
        period = request.args.get("period", "daily").lower()  # daily, weekly, monthly
        user_type = request.args.get("user_type", "student").lower()  # ✅ New filter

        # --- Build user query ---
        query = {"role": user_type} if referral_filter == "OVERALL" else {
            "referred_by": referral_filter,
            "role": user_type
        }

        users = list(users_col.find(query))
        total_users = len(users)

        # ==============================
        # 1️⃣ Referral Graph (DOC1...DOC10)
        # ==============================
        referrals = [f"DOC{i}" for i in range(1, 11)]
        graph_data = []
        for ref in referrals:
            ref_query = {"referred_by": ref, "role": user_type}
            count = users_col.count_documents(ref_query)
            graph_data.append({"referral": ref, "users": count})

        # ==============================
        # 2️⃣ Registration Trend Graph (based on user_type)
        # ==============================
        now = datetime.utcnow()
        trend_data = []

        if period == "daily":
            # Last 7 days
            for i in range(6, -1, -1):
                day = now - timedelta(days=i)
                start = datetime(day.year, day.month, day.day)
                end = start + timedelta(days=1)
                count = users_col.count_documents({
                    "createdAt": {"$gte": start, "$lt": end},
                    "role": user_type
                })
                trend_data.append({
                    "label": start.strftime("%d %b"),  # e.g., 26 Oct
                    "count": count
                })

        elif period == "weekly":
            # Last 4 weeks
            for i in range(3, -1, -1):
                week_start = now - timedelta(weeks=i + 1)
                week_end = now - timedelta(weeks=i)
                count = users_col.count_documents({
                    "createdAt": {"$gte": week_start, "$lt": week_end},
                    "role": user_type
                })
                label = f"Week {4 - i}"
                trend_data.append({"label": label, "count": count})

        elif period == "monthly":
            # Last 6 months
            for i in range(5, -1, -1):
                month = (now.month - i - 1) % 12 + 1
                year = now.year - ((now.month - i - 1) // 12)
                start = datetime(year, month, 1)
                if month == 12:
                    next_month = datetime(year + 1, 1, 1)
                else:
                    next_month = datetime(year, month + 1, 1)
                count = users_col.count_documents({
                    "createdAt": {"$gte": start, "$lt": next_month},
                    "role": user_type
                })
                trend_data.append({
                    "label": start.strftime("%b %Y"),  # e.g., Oct 2025
                    "count": count
                })

        # ==============================
        # 3️⃣ User Details Section (filtered by user_type)
        # ==============================
        recent_users = []
        for user in users[:10]:  # limit dashboard display
            user_id = str(user.get("_id", ""))
            first = user.get("first_name", "")
            last = user.get("last_name", "")
            full_name = (first + " " + last).strip() or user.get("name", "Unknown")

            # Count how many docs the user created
            doc_count = docs_col.count_documents({"user_id": user_id})

            created_at = user.get("createdAt")
            if isinstance(created_at, datetime):
                created_str = created_at.strftime("%d-%m-%Y %H:%M:%S")
            else:
                created_str = "N/A"

            recent_users.append({
                "name": full_name,
                "username": user.get("username", ""),
                "mail": user.get("email", ""),
                "docs": doc_count,
                "register_date": created_str,
                "referral": user.get("referred_by", "None"),
                "role": user.get("role", user_type.capitalize())  # ✅ Display user type
            })

        # ==============================
        # ✅ Final Response
        # ==============================
        return jsonify({
            "total_users": total_users,
            "recent_users": recent_users,
            "graph_data": graph_data,
            "trend_data": trend_data,
            "selected_referral": referral_filter,
            "period": period,
            "user_type": user_type
        }), 200

    except Exception as e:
        print("❌ Admin dashboard fetch error:", e)
        return jsonify({"error": str(e)}), 500


# ================================================================
#  🗂️  Admin Feedback Management Routes
# ================================================================

@admin_bp.route("/feedbacks", methods=["GET"])
def get_all_feedbacks():
    """Fetch all feedbacks from MongoDB"""
    try:
        db = current_app.db
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500

        feedbacks_col = db["feedbacks"]
        all_feedbacks = list(feedbacks_col.find({}, {"_id": 1, "name": 1, "email": 1, "rating": 1, "message": 1, "createdAt": 1}))

        # Convert ObjectId to string for frontend
        for fb in all_feedbacks:
            fb["_id"] = str(fb["_id"])
            if "createdAt" in fb and fb["createdAt"]:
                fb["createdAt"] = fb["createdAt"].strftime("%d-%m-%Y %H:%M")

        return jsonify({"feedbacks": all_feedbacks}), 200
    except Exception as e:
        print("❌ Error fetching feedbacks:", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/feedbacks/<feedback_id>", methods=["DELETE"])
def delete_feedback(feedback_id):
    """Delete a specific feedback by ID"""
    try:
        db = current_app.db
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500

        feedbacks_col = db["feedbacks"]
        result = feedbacks_col.delete_one({"_id": ObjectId(feedback_id)})

        if result.deleted_count == 0:
            return jsonify({"message": "Feedback not found"}), 404

        return jsonify({"message": "Feedback deleted successfully"}), 200
    except Exception as e:
        print("❌ Error deleting feedback:", e)
        return jsonify({"error": str(e)}), 500



# ================================================================
#  📩 Admin Contact Messages Management
# ================================================================
from bson import ObjectId

@admin_bp.route("/contacts", methods=["GET"])
def get_all_contacts():
    """Fetch all contact messages"""
    try:
        db = current_app.db
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500

        contact_col = db["contact_messages"]
        all_contacts = list(contact_col.find({}, {
            "_id": 1,
            "name": 1,
            "email": 1,
            "subject": 1,
            "message": 1,
            "createdAt": 1
        }))

        for c in all_contacts:
            c["_id"] = str(c["_id"])
            if "createdAt" in c and c["createdAt"]:
                c["createdAt"] = c["createdAt"].strftime("%d-%m-%Y %H:%M")

        return jsonify({"contacts": all_contacts}), 200
    except Exception as e:
        print("❌ Error fetching contacts:", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/contacts/<contact_id>", methods=["DELETE"])
def delete_contact(contact_id):
    """Delete a specific contact message"""
    try:
        db = current_app.db
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500

        contact_col = db["contact_messages"]
        result = contact_col.delete_one({"_id": ObjectId(contact_id)})

        if result.deleted_count == 0:
            return jsonify({"message": "Contact not found"}), 404

        return jsonify({"message": "Contact deleted successfully"}), 200
    except Exception as e:
        print("❌ Error deleting contact:", e)
        return jsonify({"error": str(e)}), 500



# ================================================================
# 👁️ SITE VISITORS ANALYTICS
# ================================================================
@admin_bp.route("/visitors", methods=["GET"])
def get_visitors_analytics():
    """
    Returns analytics about user activity (daily time usage, visitors, etc.)
    Requires collections:
      - user_activity  (tracks per-day total_minutes)
      - users          (basic user info)
    """
    try:
        db = current_app.db
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500

        users_col = db["users"]
        activity_col = db["user_activity"]

        today = datetime.utcnow().strftime("%Y-%m-%d")

        # 1️⃣ Total visitors (unique users who used app at least once)
        total_visitors = len(list(activity_col.distinct("user_id")))

        # 2️⃣ Today's visitors (unique users active today)
        today_visitors = len(list(activity_col.find({"date": today})))

        # 3️⃣ Total time spent today (sum of total_minutes)
        total_time_today = 0
        pipeline = [
            {"$match": {"date": today}},
            {"$group": {"_id": None, "total": {"$sum": "$total_minutes"}}}
        ]
        result = list(activity_col.aggregate(pipeline))
        if result:
            total_time_today = round(result[0]["total"], 2)

        # 4️⃣ Referral-based stats (count of users by referral)
        referral_stats = {}
        for user in users_col.find({}, {"referred_by": 1}):
            ref = user.get("referred_by", "Unknown") or "Unknown"
            referral_stats[ref] = referral_stats.get(ref, 0) + 1

        # 5️⃣ Detailed visitors table (today’s logs)
        visitors = []
        today_logs = activity_col.find({"date": today}).sort("updated_at", -1)
        for log in today_logs:
            user = users_col.find_one({"_id": log["user_id"]}, {"first_name": 1, "last_name": 1, "email": 1, "referred_by": 1})
            if not user:
                continue

            visitors.append({
                "_id": str(log["_id"]),
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "Guest",
                "email": user.get("email", "N/A"),
                "referral": user.get("referred_by", "N/A"),
                "visit_start": log.get("created_at", "").strftime("%H:%M") if log.get("created_at") else "N/A",
                "visit_end": log.get("updated_at", "").strftime("%H:%M") if log.get("updated_at") else "N/A",
                "duration_minutes": round(log.get("total_minutes", 0), 2)
            })

        # ✅ Final response
        return jsonify({
            "total_visitors": total_visitors,
            "today_visitors": today_visitors,
            "today_time_spent": total_time_today,
            "referral_stats": referral_stats,
            "visitors": visitors
        }), 200

    except Exception as e:
        print("❌ Error fetching visitors:", e)
        return jsonify({"error": str(e)}), 500