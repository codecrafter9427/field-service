package com.businessai.fieldservice.agenda

import com.businessai.fieldservice.models.AgendaDay
import com.businessai.fieldservice.models.WorkOrderSummary

/**
 * Technician agenda repository stub.
 * Returns fictional placeholder jobs until API + seed are implemented.
 * Offline sync is intentionally not implemented in this scaffold.
 */
class AgendaRepository {
    fun todayAgenda(): AgendaDay {
        return AgendaDay(
            dateIso = "2026-11-26",
            jobs = listOf(
                WorkOrderSummary(
                    id = "00000000-0000-4000-8000-000000000101",
                    title = "HVAC filter check (demo)",
                    customerName = "Acme Facilities (demo)",
                    status = "Scheduled",
                    scheduledStartIso = "2026-11-26T09:00:00Z",
                    priority = "Normal",
                ),
                WorkOrderSummary(
                    id = "00000000-0000-4000-8000-000000000102",
                    title = "Pump seal inspection (demo)",
                    customerName = "River Plant (demo)",
                    status = "En Route",
                    scheduledStartIso = "2026-11-26T13:00:00Z",
                    priority = "High",
                ),
            ),
        )
    }
}
