package com.example.app

sealed class Op {
    data class Begin(val txnId: String) : Op()
    data class Add(val txnId: String, val container: String, val fragment: String) : Op()
    data class AddChild(val txnId: String, val parent: String, val childContainer: String, val child: String) : Op()
    data class Replace(val txnId: String, val container: String, val fragment: String) : Op()
    data class Remove(val txnId: String, val fragment: String) : Op()
    data class Hide(val txnId: String, val fragment: String) : Op()
    data class Show(val txnId: String, val fragment: String) : Op()
    data class Detach(val txnId: String, val fragment: String) : Op()
    data class Attach(val txnId: String, val fragment: String) : Op()
    data class SetMax(val txnId: String, val fragment: String, val state: String) : Op()
    data class Save(val fragment: String, val key: String, val value: String) : Op()
    data class VmPut(val fragment: String, val key: String, val value: String) : Op()
    data class BindPut(val fragment: String, val key: String, val value: String) : Op()
    data class AddToBackStack(val txnId: String, val name: String?) : Op()
    data class Commit(val txnId: String) : Op()
    data class Pop(val name: String?) : Op()
    object Rotate : Op()
    object Query : Op()
}

data class Scenario(val ops: List<Op>)
