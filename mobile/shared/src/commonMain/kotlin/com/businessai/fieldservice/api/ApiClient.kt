package com.businessai.fieldservice.api

import com.businessai.fieldservice.models.AgendaDay
import com.businessai.fieldservice.models.ChecklistItemView
import com.businessai.fieldservice.models.ChecklistView
import com.businessai.fieldservice.models.JobDetail
import com.businessai.fieldservice.models.JobNote
import com.businessai.fieldservice.models.LoginSession
import com.businessai.fieldservice.models.WorkOrderSummary

/**
 * Live FastAPI client for technician agenda + job detail + M5 writes.
 *
 * Emulator loopback: `http://10.0.2.2:8003/api/v1`
 * Physical device: use your LAN IP, e.g. `http://192.168.x.x:8003/api/v1`
 */
class ApiClient(
    private val baseUrl: String = DEFAULT_BASE_URL,
    private val transport: HttpTransport = HttpTransport(),
) {
    var accessToken: String? = null
        private set

    fun healthHint(): String =
        "Point device/emulator at $baseUrl (host loopback via 10.0.2.2 on Android emulator)."

    fun demoLogin(email: String, password: String): LoginSession {
        val body = """{"email":"${JsonLite.escape(email)}","password":"${JsonLite.escape(password)}"}"""
        val raw =
            transport.request(
                method = "POST",
                url = "$baseUrl/auth/demo-login",
                body = body,
            )
        val token = JsonLite.requiredString(raw, "access_token")
        accessToken = token
        return LoginSession(
            accessToken = token,
            displayName = JsonLite.stringField(raw, "display_name") ?: email,
            role = JsonLite.stringField(raw, "role") ?: "technician",
            email = JsonLite.stringField(raw, "email") ?: email,
        )
    }

    fun setToken(token: String) {
        accessToken = token
    }

    fun fetchAgenda(technicianId: String? = null): AgendaDay {
        val token = requireToken()
        val suffix = if (technicianId != null) "?technician_id=$technicianId" else ""
        val raw =
            transport.request(
                method = "GET",
                url = "$baseUrl/assignments/agenda$suffix",
                headers = authHeaders(token),
            )
        val jobs =
            JsonLite.rootArray(raw).map { obj ->
                WorkOrderSummary(
                    id = JsonLite.requiredString(obj, "work_order_id"),
                    title = JsonLite.stringField(obj, "work_order_title") ?: "Job",
                    customerName = JsonLite.stringField(obj, "technician_name")?.let { "Assigned · $it" }
                        ?: "Customer",
                    status = JsonLite.stringField(obj, "work_order_status") ?: "scheduled",
                    scheduledStartIso = JsonLite.stringField(obj, "scheduled_start"),
                    priority = "normal",
                )
            }
        return AgendaDay(
            dateIso = "live",
            jobs = jobs,
            source = "api",
        )
    }

    fun fetchJobDetail(workOrderId: String): JobDetail {
        val token = requireToken()
        val raw =
            transport.request(
                method = "GET",
                url = "$baseUrl/work-orders/$workOrderId",
                headers = authHeaders(token),
            )
        val notesRaw =
            runCatching {
                transport.request(
                    method = "GET",
                    url = "$baseUrl/work-orders/$workOrderId/activities",
                    headers = authHeaders(token),
                )
            }.getOrDefault("[]")
        val checklistsRaw =
            runCatching {
                transport.request(
                    method = "GET",
                    url = "$baseUrl/checklists?work_order_id=$workOrderId",
                    headers = authHeaders(token),
                )
            }.getOrDefault("[]")

        val notes =
            JsonLite.rootArray(notesRaw).mapNotNull { obj ->
                val text = JsonLite.stringField(obj, "note") ?: return@mapNotNull null
                if (text.isBlank()) return@mapNotNull null
                JobNote(
                    id = JsonLite.stringField(obj, "id"),
                    text = text,
                    activityType = JsonLite.stringField(obj, "activity_type") ?: "note",
                    clientOperationId = JsonLite.stringField(obj, "client_operation_id"),
                )
            }
        val checklists =
            JsonLite.rootArray(checklistsRaw).map { cl ->
                ChecklistView(
                    id = JsonLite.requiredString(cl, "id"),
                    name = JsonLite.stringField(cl, "name") ?: "Checklist",
                    items =
                        JsonLite.objectArray(cl, "items").map { item ->
                            ChecklistItemView(
                                id = JsonLite.requiredString(item, "id"),
                                label = JsonLite.stringField(item, "label") ?: "Item",
                                isCompleted = JsonLite.boolField(item, "is_completed") ?: false,
                                updatedAt = JsonLite.stringField(item, "updated_at") ?: "",
                            )
                        },
                )
            }

        return JobDetail(
            id = JsonLite.requiredString(raw, "id"),
            title = JsonLite.requiredString(raw, "title"),
            status = JsonLite.requiredString(raw, "status"),
            priority = JsonLite.stringField(raw, "priority") ?: "normal",
            description = JsonLite.stringField(raw, "description"),
            customerId = JsonLite.requiredString(raw, "customer_id"),
            technicianName = JsonLite.stringField(raw, "technician_name"),
            scheduledStartIso = JsonLite.stringField(raw, "scheduled_start"),
            scheduledEndIso = JsonLite.stringField(raw, "scheduled_end"),
            updatedAt = JsonLite.requiredString(raw, "updated_at"),
            notes = notes,
            checklists = checklists,
        )
    }

    fun postNote(
        workOrderId: String,
        note: String,
        clientOperationId: String,
        clientOccurredAt: String,
    ): String {
        val token = requireToken()
        val body =
            """{"note":"${JsonLite.escape(note)}","client_operation_id":"$clientOperationId","client_occurred_at":"$clientOccurredAt"}"""
        return transport.request(
            method = "POST",
            url = "$baseUrl/work-orders/$workOrderId/notes",
            headers = authHeaders(token),
            body = body,
        )
    }

    fun patchStatus(
        workOrderId: String,
        status: String,
        baseUpdatedAt: String,
    ): String {
        val token = requireToken()
        val body =
            """{"status":"$status","base_updated_at":"$baseUpdatedAt"}"""
        return transport.request(
            method = "PATCH",
            url = "$baseUrl/work-orders/$workOrderId",
            headers = authHeaders(token),
            body = body,
        )
    }

    fun patchChecklistItem(
        itemId: String,
        isCompleted: Boolean,
        baseUpdatedAt: String,
    ): String {
        val token = requireToken()
        val body =
            """{"is_completed":$isCompleted,"base_updated_at":"$baseUpdatedAt"}"""
        return transport.request(
            method = "PATCH",
            url = "$baseUrl/checklists/items/$itemId",
            headers = authHeaders(token),
            body = body,
        )
    }

    private fun requireToken(): String =
        accessToken ?: error("Call demoLogin() or setToken() before API requests")

    private fun authHeaders(token: String): Map<String, String> =
        mapOf("Authorization" to "Bearer $token", "Accept" to "application/json")

    companion object {
        const val DEFAULT_BASE_URL = "http://10.0.2.2:8003/api/v1"
        const val DEMO_TECH_EMAIL = "tech@demo.local"
        const val DEMO_PASSWORD = "demo"
    }
}

/** Parsed 409 conflict body for sync drain. */
class ConflictException(
    val statusCode: Int,
    val serverSnapshotJson: String?,
    message: String,
) : Exception(message)

fun HttpException.toConflictOrRethrow(): Nothing {
    if (statusCode == 409) {
        val server =
            JsonLite.nestedObject(message, "details", "server")
                ?: JsonLite.objectField(message, "server")
        throw ConflictException(statusCode, server, message)
    }
    throw this
}
