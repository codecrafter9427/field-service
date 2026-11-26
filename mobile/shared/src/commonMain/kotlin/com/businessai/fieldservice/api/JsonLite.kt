package com.businessai.fieldservice.api

/**
 * Tiny JSON helpers for demo payloads — enough for agenda/job detail without
 * adding a serialization dependency to the KMP skeleton.
 */
internal object JsonLite {
    fun stringField(json: String, key: String): String? {
        val patterns =
            listOf(
                """"$key"\s*:\s*"((?:\\.|[^"\\])*)"""".toRegex(),
                """"$key"\s*:\s*null""".toRegex(),
            )
        val quoted = patterns[0].find(json) ?: return if (patterns[1].containsMatchIn(json)) null else null
        return quoted.groupValues[1]
            .replace("\\\"", "\"")
            .replace("\\\\", "\\")
            .replace("\\n", "\n")
    }

    fun requiredString(json: String, key: String): String =
        stringField(json, key) ?: error("Missing JSON string field: $key")

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
