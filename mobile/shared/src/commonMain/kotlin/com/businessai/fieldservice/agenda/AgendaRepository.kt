package com.businessai.fieldservice.agenda

import com.businessai.fieldservice.api.ApiClient
import com.businessai.fieldservice.models.AgendaDay
import com.businessai.fieldservice.models.JobDetail
import com.businessai.fieldservice.models.WorkOrderSummary

/**
 * Technician agenda + job detail repository.
 *
 * Tries live API (`ApiClient`); falls back to demo stubs if the backend is
 * unreachable so Android Studio previews still render.
 */
class AgendaRepository(
    private val api: ApiClient = ApiClient(),
    private val preferLive: Boolean = true,
) {
    fun todayAgenda(
        email: String = ApiClient.DEMO_TECH_EMAIL,
        password: String = ApiClient.DEMO_PASSWORD,
    ): AgendaDay {
        if (preferLive) {
            try {
                api.demoLogin(email, password)
                return api.fetchAgenda()
            } catch (_: Exception) {
                // Fall through to demo stubs
            }
        }
        return demoAgenda()
    }

    fun jobDetail(
        workOrderId: String,
        email: String = ApiClient.DEMO_TECH_EMAIL,
        password: String = ApiClient.DEMO_PASSWORD,
    ): JobDetail {
        if (preferLive) {
            try {
                if (api.accessToken == null) {
                    api.demoLogin(email, password)
                }
                return api.fetchJobDetail(workOrderId)
            } catch (_: Exception) {
                // Fall through
            }
        }
        return demoJobDetail(workOrderId)
    }

    fun healthHint(): String = api.healthHint()

    private fun demoAgenda(): AgendaDay =
        AgendaDay(
            dateIso = "2026-11-26",
            source = "demo",
            jobs =
                listOf(
                    WorkOrderSummary(
                        id = "00000000-0000-4000-8000-000000000101",
                        title = "HVAC filter check (demo)",
                        customerName = "Acme Facilities (demo)",
                        status = "scheduled",
                        scheduledStartIso = "2026-11-26T09:00:00Z",
                        priority = "normal",
                    ),
                    WorkOrderSummary(
                        id = "00000000-0000-4000-8000-000000000102",
                        title = "Pump seal inspection (demo)",
                        customerName = "River Plant (demo)",
                        status = "en_route",
                        scheduledStartIso = "2026-11-26T13:00:00Z",
                        priority = "high",
                    ),
                ),
        )

    private fun demoJobDetail(workOrderId: String): JobDetail =
        JobDetail(
            id = workOrderId,
            title = "Demo job detail",
            status = "scheduled",
            priority = "normal",
            description = "Offline/demo fallback — start API on :8003 for live data.",
            customerId = "00000000-0000-4000-8000-000000000001",
            technicianName = "Demo Tech",
            scheduledStartIso = "2026-11-26T09:00:00Z",
            scheduledEndIso = "2026-11-26T11:00:00Z",
            notes = listOf("Demo note — connect to API for real activities."),
        )
}
