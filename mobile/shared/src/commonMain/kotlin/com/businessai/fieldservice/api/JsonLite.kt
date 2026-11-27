package com.businessai.fieldservice.api

/**
 * Tiny JSON helpers for demo payloads — enough for agenda/job detail/sync
 * without adding a serialization dependency to the KMP skeleton.
 */
internal object JsonLite {
    fun stringField(json: String, key: String): String? {
        val quoted =
            """"$key"\s*:\s*"((?:\\.|[^"\\])*)"""".toRegex().find(json)
        if (quoted != null) {
            return quoted.groupValues[1]
                .replace("\\\"", "\"")
                .replace("\\\\", "\\")
                .replace("\\n", "\n")
        }
        if (""""$key"\s*:\s*null""".toRegex().containsMatchIn(json)) return null
        return null
    }

    fun requiredString(json: String, key: String): String =
        stringField(json, key) ?: error("Missing JSON string field: $key")

    fun boolField(json: String, key: String): Boolean? {
        val m = """"$key"\s*:\s*(true|false)""".toRegex().find(json) ?: return null
        return m.groupValues[1] == "true"
    }

    fun escape(value: String): String =
        value
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")

    fun objectArray(json: String, arrayKey: String): List<String> {
        val marker = """"$arrayKey"\s*:\s*\[""".toRegex().find(json) ?: return emptyList()
        val start = marker.range.last + 1
        var depth = 1
        var i = start
        while (i < json.length && depth > 0) {
            when (json[i]) {
                '[' -> depth++
                ']' -> depth--
            }
            i++
        }
        val inner = json.substring(start, i - 1)
        return splitObjects(inner)
    }

    fun rootArray(json: String): List<String> {
        val trimmed = json.trim()
        if (!trimmed.startsWith("[")) return emptyList()
        return splitObjects(trimmed.removePrefix("[").removeSuffix("]"))
    }

    /** Extract nested `"details":{"server":{...}}` object text from a 409 body. */
    fun nestedObject(json: String, outerKey: String, innerKey: String): String? {
        val outer = objectField(json, outerKey) ?: return null
        return objectField(outer, innerKey)
    }

    fun objectField(json: String, key: String): String? {
        val marker = """"$key"\s*:\s*\{""".toRegex().find(json) ?: return null
        val start = marker.range.last
        var depth = 0
        var i = start
        while (i < json.length) {
            when (json[i]) {
                '{' -> depth++
                '}' -> {
                    depth--
                    if (depth == 0) return json.substring(start, i + 1)
                }
            }
            i++
        }
        return null
    }

    private fun splitObjects(inner: String): List<String> {
        val out = mutableListOf<String>()
        var depth = 0
        var start = -1
        for (i in inner.indices) {
            when (inner[i]) {
                '{' -> {
                    if (depth == 0) start = i
                    depth++
                }
                '}' -> {
                    depth--
                    if (depth == 0 && start >= 0) {
                        out += inner.substring(start, i + 1)
                        start = -1
                    }
                }
            }
        }
        return out
    }
}
