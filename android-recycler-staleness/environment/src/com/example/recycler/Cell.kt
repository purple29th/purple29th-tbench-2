package com.example.recycler

class Cell(val id: String) {
    var itemId: String? = null
        private set
    var title: String = ""
        private set
    var imageUrl: String? = null
        private set
    var bindingToken: Long = 0L
        private set

    fun bind(itemId: String, title: String, nextToken: Long) {
        this.itemId = itemId
        this.title = title
        this.imageUrl = null
        this.bindingToken = nextToken
    }

    fun recycle(nextToken: Long) {
        this.itemId = null
        this.title = ""
        this.imageUrl = null
        this.bindingToken = nextToken
    }

    fun bumpTokenAfterApply(nextToken: Long) {
        this.bindingToken = nextToken
    }

    fun isBound(): Boolean = itemId != null

    fun applyImage(url: String, expectedToken: Long): Boolean {
        if (bindingToken != expectedToken) return false
        imageUrl = url
        return true
    }
}
