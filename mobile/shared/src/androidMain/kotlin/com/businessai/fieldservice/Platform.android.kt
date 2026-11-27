package com.businessai.fieldservice

import java.time.Instant
import java.util.UUID

actual fun platformName(): String = "Android"

actual fun randomUuid(): String = UUID.randomUUID().toString()

actual fun currentTimeIso(): String = Instant.now().toString()
