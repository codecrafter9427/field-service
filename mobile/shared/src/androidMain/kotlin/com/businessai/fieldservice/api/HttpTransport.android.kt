package com.businessai.fieldservice.api

import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

actual class HttpTransport {
    actual fun request(
        method: String,
        url: String,
        headers: Map<String, String>,
        body: String?,
    ): String {
        val connection = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 12_000
            readTimeout = 20_000
            doInput = true
            headers.forEach { (k, v) -> setRequestProperty(k, v) }
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                OutputStreamWriter(outputStream, Charsets.UTF_8).use { it.write(body) }
            }
        }
        val code = connection.responseCode
        val stream =
            if (code in 200..299) connection.inputStream else connection.errorStream
        val text =
            stream?.let { BufferedReader(InputStreamReader(it, Charsets.UTF_8)).use { r -> r.readText() } }
                ?: ""
        if (code !in 200..299) {
            throw HttpException(code, text.ifBlank { "HTTP $code" })
        }
        return text
    }
}
