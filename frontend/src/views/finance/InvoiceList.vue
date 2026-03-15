<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

interface InvoiceItem {
  id: string
  payment_id: string | null
  customer_name: string
  quote_no: string | null
  invoice_type: string
  invoice_title: string
  tax_no: string | null
  invoice_amount: number
  invoice_no: string | null
  issue_date: string | null
  status: string
  remark: string | null
  created_at: string
}

const INVOICE_TYPES = ['增值税普通发票', '增值税专用发票']
const INVOICE_STATUSES = ['待开具', '已开具', '已邮寄', '已上传']

const loading = ref(false)
const list = ref<InvoiceItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '' })

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await request.get<any, { data: InvoiceItem[]; total: number }>('/invoices', { params })
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.status = ''; query.keyword = ''; query.page = 1; loadList() }

// ── 新增/编辑弹窗 ─────────────────────────────────────────────
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<string | null>(null)
const form = reactive({
  customer_name: '',
  quote_no: '',
  invoice_type: '增值税普通发票',
  invoice_title: '',
  tax_no: '',
  invoice_amount: 0,
  invoice_no: '',
  issue_date: '',
  status: '待开具',
  remark: '',
})

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    customer_name: '', quote_no: '', invoice_type: '增值税普通发票',
    invoice_title: '', tax_no: '', invoice_amount: 0,
    invoice_no: '', issue_date: new Date().toISOString().slice(0, 10),
    status: '待开具', remark: '',
  })
  dialogVisible.value = true
}

function openEdit(row: InvoiceItem) {
  editingId.value = row.id
  Object.assign(form, {
    customer_name: row.customer_name,
    quote_no: row.quote_no || '',
    invoice_type: row.invoice_type,
    invoice_title: row.invoice_title,
    tax_no: row.tax_no || '',
    invoice_amount: row.invoice_amount,
    invoice_no: row.invoice_no || '',
    issue_date: row.issue_date || '',
    status: row.status,
    remark: row.remark || '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.customer_name) { ElMessage.warning('请填写客户名称'); return }
  if (!form.invoice_title) { ElMessage.warning('请填写发票抬头'); return }
  if (!form.invoice_amount || form.invoice_amount <= 0) { ElMessage.warning('请填写开票金额'); return }
  saving.value = true
  try {
    const payload = {
      customer_name: form.customer_name,
      quote_no: form.quote_no || null,
      invoice_type: form.invoice_type,
      invoice_title: form.invoice_title,
      tax_no: form.tax_no || null,
      invoice_amount: form.invoice_amount,
      invoice_no: form.invoice_no || null,
      issue_date: form.issue_date || null,
      status: form.status,
      remark: form.remark || null,
    }
    if (editingId.value) {
      await request.put(`/invoices/${editingId.value}`, payload)
      ElMessage.success('已更新')
    } else {
      await request.post('/invoices', payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: InvoiceItem) {
  await ElMessageBox.confirm('确认删除该发票记录？', '删除确认', { type: 'warning' })
  await request.delete(`/invoices/${row.id}`)
  ElMessage.success('已删除')
  loadList()
}

function statusTagType(s: string) {
  if (s === '已上传') return 'success'
  if (s === '已开具' || s === '已邮寄') return 'primary'
  return 'info'
}

function fmt(v: number) {
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(() => loadList())
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>发票管理</h2>
      <el-button type="primary" @click="openCreate">新增发票</el-button>
    </div>

    <el-card shadow="never" style="margin-bottom:12px">
      <el-form inline>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" style="width:110px">
            <el-option v-for="s in INVOICE_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="query.keyword" clearable placeholder="客户/报价单号/发票号" style="width:200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="客户名称" prop="customer_name" min-width="160" />
        <el-table-column label="报价单号" prop="quote_no" width="140" />
        <el-table-column label="发票类型" prop="invoice_type" width="140" />
        <el-table-column label="发票抬头" prop="invoice_title" min-width="160" show-overflow-tooltip />
        <el-table-column label="开票金额" width="130" align="right">
          <template #default="{ row }">¥ {{ fmt(row.invoice_amount) }}</template>
        </el-table-column>
        <el-table-column label="发票号码" prop="invoice_no" width="140" />
        <el-table-column label="开票日期" prop="issue_date" width="110" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑发票' : '新增发票'" width="560px" destroy-on-close>
      <el-form :model="form" label-width="90px">
        <el-form-item label="客户名称" required>
          <el-input v-model="form.customer_name" placeholder="客户公司名称" />
        </el-form-item>
        <el-form-item label="报价单号">
          <el-input v-model="form.quote_no" placeholder="关联报价单号（可选）" />
        </el-form-item>
        <el-form-item label="发票类型">
          <el-select v-model="form.invoice_type" style="width:100%">
            <el-option v-for="t in INVOICE_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="发票抬头" required>
          <el-input v-model="form.invoice_title" placeholder="开票抬头" />
        </el-form-item>
        <el-form-item label="纳税人识别号">
          <el-input v-model="form.tax_no" placeholder="税号（专票必填）" />
        </el-form-item>
        <el-form-item label="开票金额" required>
          <el-input-number v-model="form.invoice_amount" :min="0.01" :precision="2" style="width:100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="发票号码">
          <el-input v-model="form.invoice_no" placeholder="发票号码" />
        </el-form-item>
        <el-form-item label="开票日期">
          <el-date-picker v-model="form.issue_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option v-for="s in INVOICE_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="可选" />
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
