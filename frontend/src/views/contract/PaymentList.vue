<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

interface PaymentItem {
  id: string
  quotation_id: string
  quote_no: string
  customer_name: string | null
  total_amount: number
  received_amount: number
  status: string
  received_date: string | null
  payment_method: string | null
  remark: string | null
}

const loading = ref(false)
const list = ref<PaymentItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '' })

const statusOptions = ['待收款', '部分收款', '已收款']
const methodOptions = ['对公转账', '现金', '支票', '其他']

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await request.get<any, { data: PaymentItem[]; total: number }>('/quotation-payments', { params })
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.status = ''; query.keyword = ''; query.page = 1; loadList() }

// ── 收款弹窗 ─────────────────────────────────────────────────
const dialogVisible = ref(false)
const saving = ref(false)
const editingItem = ref<PaymentItem | null>(null)
const form = reactive({
  received_amount: 0,
  received_date: '',
  payment_method: '对公转账',
  remark: '',
})

async function handleDelete(row: PaymentItem) {
  await ElMessageBox.confirm('确认删除该收款记录？', '删除确认', { type: 'warning' })
  await request.delete(`/quotation-payments/${row.id}`)
  ElMessage.success('已删除')
  loadList()
}

function openCollect(row: PaymentItem) {
  editingItem.value = row
  form.received_amount = row.received_amount || row.total_amount
  form.received_date = new Date().toISOString().slice(0, 10)
  form.payment_method = row.payment_method || '对公转账'
  form.remark = row.remark || ''
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.received_date) { ElMessage.warning('请选择收款日期'); return }
  saving.value = true
  try {
    await request.put(`/quotation-payments/${editingItem.value!.id}`, {
      received_amount: form.received_amount,
      received_date: form.received_date,
      payment_method: form.payment_method,
      remark: form.remark || null,
    })
    ElMessage.success('收款已登记')
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

function statusTagType(s: string) {
  if (s === '已收款') return 'success'
  if (s === '部分收款') return 'warning'
  return 'info'
}

function fmt(v: number) {
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

onMounted(() => loadList())
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>收款管理</h2>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" style="margin-bottom:12px">
      <el-form inline>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" style="width:110px">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户/报价单号">
          <el-input v-model="query.keyword" clearable placeholder="搜索" style="width:180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="报价单号" prop="quote_no" width="150" />
        <el-table-column label="客户" prop="customer_name" min-width="160" />
        <el-table-column label="合同金额" width="130" align="right">
          <template #default="{ row }">¥ {{ fmt(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="已收金额" width="130" align="right">
          <template #default="{ row }">
            <span :style="row.received_amount > 0 ? 'color:#67c23a;font-weight:600' : ''">
              ¥ {{ fmt(row.received_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="待收金额" width="130" align="right">
          <template #default="{ row }">
            <span :style="row.total_amount - row.received_amount > 0 ? 'color:#e6a23c;font-weight:600' : ''">
              ¥ {{ fmt(row.total_amount - row.received_amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收款日期" prop="received_date" width="110" />
        <el-table-column label="收款方式" prop="payment_method" width="100" />
        <el-table-column label="备注" prop="remark" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openCollect(row)">登记收款</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top:12px;justify-content:flex-end"
        @current-change="loadList"
      />
    </el-card>

    <!-- 收款弹窗 -->
    <el-dialog v-model="dialogVisible" title="登记收款" width="420px">
      <div v-if="editingItem" style="margin-bottom:12px;color:#606266;font-size:13px">
        报价单：<b>{{ editingItem.quote_no }}</b>　客户：<b>{{ editingItem.customer_name }}</b><br/>
        合同金额：<b>¥ {{ fmt(editingItem.total_amount) }}</b>
      </div>
      <el-form label-width="90px">
        <el-form-item label="收款金额" required>
          <el-input-number v-model="form.received_amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="收款日期" required>
          <el-date-picker v-model="form.received_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="收款方式">
          <el-select v-model="form.payment_method" style="width:100%">
            <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
</style>
