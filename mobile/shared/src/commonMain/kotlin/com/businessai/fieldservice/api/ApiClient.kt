package com.businessai.fieldservice.api

import com.businessai.fieldservice.models.AgendaDay
import com.businessai.fieldservice.models.JobDetail
import com.businessai.fieldservice.models.LoginSession
import com.businessai.fieldservice.models.WorkOrderSummary

/**
 * Live FastAPI client for technician agenda + job detail.
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
        val body = """{"email":"${email.escapeJson()}","password":"${password.escapeJson()}"}"""
        val raw =
            transport.request(
                method = "POST",
                url = "$baseUrl/auth/demo-login",
                body = body,
            )
        val token = JsonLite.requiredString(raw, "access_token")
        accessToken = token
        // user object nested — extract best-effort fields from whole payload
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
        val notes =
            JsonLite.rootArray(notesRaw)
                .mapNotNull { JsonLite.stringField(it, "note") }
                .filter { it.isNotBlank() }
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
            notes = notes,
        )
    }

    private fun requireToken(): String =
        accessToken ?: error("Call demoLogin() or setToken() before API requests")

    private fun authHeaders(token: String): Map<String, String> =
        mapOf("Authorization" to "Bearer $token", "Accept" to "application/json")

    private fun String.escapeJson(): String =
        replace("\\", "\\\\").replace("\"", "\\\"")

    companion object {
        const val DEFAULT_BASE_URL = "http://10.0.2.2:8003/api/v1"
        const val DEMO_TECH_EMAIL = "tech@demo.local"
        const val DEMO_PASSWORD = "demo"
    }
}
