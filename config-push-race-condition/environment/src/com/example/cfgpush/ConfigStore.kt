package com.example.cfgpush

class ConfigStore {
    private val values = mutableMapOf<String, String>()
    private val observers = mutableListOf<Observer>()
    private val snapshots = mutableMapOf<String, Snapshot>()
    private val readerVersions = mutableMapOf<String, Long>()
    private val notifications = mutableListOf<String>()

    var version: Long = 0
        private set

    fun push(newVersion: Long, updates: Map<String, String>) {
        values.putAll(updates)
        version = newVersion
        emitNotifications(updates.keys, newVersion)
    }

    fun read(readerId: String, key: String): String? = values[key]

    fun beginSnapshot(readerId: String) {
        snapshots[readerId] = Snapshot(version, values.toMap())
    }

    fun readFromSnapshot(readerId: String, key: String): String? = values[key]

    fun endSnapshot(readerId: String) {
        snapshots.remove(readerId)
    }

    fun subscribe(observerId: String, keys: Set<String>) {
        observers += Observer(observerId, keys)
    }

    fun unsubscribe(observerId: String) {
        observers.firstOrNull { it.id == observerId }
    }

    fun render(): String = buildString {
        appendStore(this)
        appendReaders(this)
        appendNotifications(this)
    }

    private fun emitNotifications(changedKeys: Set<String>, atVersion: Long) {
        for (observer in observers) {
            for (key in changedKeys) {
                if (key !in observer.keys) continue
                notifications += formatNotification(observer.id, listOf(key), atVersion)
            }
        }
    }

    private fun appendStore(builder: StringBuilder) {
        builder.append("store version=$version\n")
        for (key in values.keys.sorted()) {
            builder.append("  $key=${values.getValue(key)}\n")
        }
    }

    private fun appendReaders(builder: StringBuilder) {
        builder.append("readers:\n")
        for (readerId in readerVersions.keys.sorted()) {
            builder.append("  $readerId version=${readerVersions.getValue(readerId)}\n")
        }
    }

    private fun appendNotifications(builder: StringBuilder) {
        builder.append("notifications:\n")
        for (entry in notifications) {
            builder.append("  $entry\n")
        }
    }

    private fun formatNotification(observerId: String, keys: Collection<String>, atVersion: Long): String =
        "$observerId:keys=${keys.sorted().joinToString(separator = ",")}:v$atVersion"
}
