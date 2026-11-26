package com.businessai.fieldservice.api

/**
 * HTTP client stub — wire to FastAPI /api/v1 when CRUD exists.
 */
class ApiClient(
    private val baseUrl: String = "http://10.0.2.2:8003/api/v1",
) {
    fun healthHint(): String =
        "Point device/emulator at $baseUrl (host loopback via 10.0.2.2 on Android emulator)."
}
