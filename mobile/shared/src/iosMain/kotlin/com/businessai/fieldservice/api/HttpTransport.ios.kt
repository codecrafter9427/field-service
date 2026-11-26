package com.businessai.fieldservice.api

/**
 * iOS UI/networking follow-up — throws until native HTTP is wired.
 */
actual class HttpTransport {
    actual fun request(
        method: String,
        url: String,
        headers: Map<String, String>,
        body: String?,
    ): String {
        throw HttpException(
            statusCode = 501,
            message = "iOS HTTP transport Coming Soon — use Android for live API demos.",
        )
    }
}
