package com.businessai.fieldservice.api

/**
 * Minimal expect/actual HTTP transport — no paid SDKs.
 * Android uses HttpURLConnection; iOS is a later follow-up stub.
 */
expect class HttpTransport() {
    fun request(
        method: String,
        url: String,
        headers: Map<String, String> = emptyMap(),
        body: String? = null,
    ): String
}

class HttpException(
    val statusCode: Int,
    message: String,
) : Exception(message)
