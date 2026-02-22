<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { contractApi, type PaymentPlanListItem, type ContractDetail } from '@/api/contract'

const router = useRouter()

const loading = ref(false)
const list = ref<PaymentPlanListItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '', keyword: '', overdue: false })

const planStatusOptions = ['待支付', '部分支付', '已支付', '已逾期']

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    if (query.overdue) params.overdue = true
    const res = await contractApi.listAllPaymentPlans(params as any)
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; loadList() }
function handleReset() { query.status = ''; query.keyword = ''; query.overdue = false; query.page = 1; loadList() }

function goContract(row: PaymentPlanListItem) {
  router.push(`/contracts/${row.contract_id}`)
}

// ── 收款弹窗 ────────────────────────────────────────────────
const collectVisible = ref(false)
const collectPlan = ref<PaymentPlanListItem | null>(null)
const collectContract = ref<ContractDetail | null>(null)
const collectForm = reactive({
  received_amount: 0,
  received_date: '',
  payment_method: '对公转账',
  bank_reference: '',
  remark: '',
})
const collectSaving = ref(false)
const paymentMethodOptions = ['对公转账', '现金', '支票', '其他']

async function openCollect(row: PaymentPlanListItem) {
  collectPlan.value = row
  const res = await contractApi.get(row.contract_id)
  collectContract.value = res.data
  Object.assign(collectForm, {
    received_amount: Number(row.plan_amount) - Number(row.received_amount),
    received_date: '',
    payment_method: '对公转账',
    bank_reference: '',
    remark: '',
  })
  collectVisible.value = true
}

async function handleCollect() {
  if (!collectForm.received_date) { ElMessage.warning('请选择收款日期'); return }
  if (!collectForm.received_amount) { ElMessage.warning('请填写收款金额'); return }
  collectSaving.value = true
  try {
    await contractApi.addPaymentRecord(collectPlan.value!.contract_id, {
      plan_id: collectPlan.value!.id,
      ...collectForm,
    })
    ElMessage.success('收款已登记')
    collectVisible.value = false
    loadList()
  } finally {
    collectSaving.value = false
  }
}

const planStatusType = (s: string) =>
  ({ '待支付': 'info', '部分支付': 'warning', '已支付': 'success', '已逾期': 'danger' }[s] ?? '') as any

function isOverdue(row: PaymentPlanListItem) {
  return row.due_date && row.due_date < new Date().toISOString().slice(0, 10) && row.status !== '已支付'
}

onMounted(loadList)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="7">
          <el-input v-model="query.keyword" placeholder="搜索合同名称/编号" clearable @keyup.enter="handleSearch" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="query.status" placeholder="付款状态" clearable style="width:100%">
            <el-option v-for="s in planStatusOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-checkbox v-model="query.overdue" @change="handleSearch">仅逾期</el-checkbox>
        </el-col>
        <el-col :span="5">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" row-key="id" style="width:100%">
        <el-table-column prop="contract_no" label="合同编号" width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="goContract(row)">{{ row.contract_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="contract_name" label="合同名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="期次" width="60" align="center">
          <template #default="{ row }">第{{ row.installment_no }}期</template>
        </el-table-column>
        <el-table-column prop="description" label="说明" width="110" />
        <el-table-column prop="plan_amount" label="计划金额" width="120" align="right">
          <template #default="{ row }">{{ Number(row.plan_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="received_amount" label="已收款" width="120" align="right">
          <template #default="{ row }">
            <span :style="{ color: Number(row.received_amount) > 0 ? '#67c23a' : '#909399' }">
              {{ Number(row.received_amount).toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="待收余额" width="120" align="right">
          <template #default="{ row }">
            <span :style="{ color: (Number(row.plan_amount) - Number(row.received_amount)) > 0 ? '#f56c6c' : '#67c23a' }">
              {{ (Number(row.plan_amount) - Number(row.received_amount)).toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="应付日期" width="110">
          <template #default="{ row }">
            <span :style="{ color: isOverdue(row) ? '#f56c6c' : '' }">{{ row.due_date }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="planStatusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== '已支付'"
              size="small" link type="primary"
              @click="openCollect(row)"
            >登记收款</el-button>
            <el-button
              v-else size="small" link type="success" disabled
            >已收款</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top:16px;justify-content:flex-end;display:flex"
        @change="loadList"
      />
    </el-card>

    <!-- 登记收款弹窗 -->
    <el-dialog v-model="collectVisible" title="登记收款" width="420px" destroy-on-close>
      <div v-if="collectPlan" style="margin-bottom:12px;color:#606266;font-size:13px">
        <div>合同：<strong>{{ collectPlan.contract_no }}</strong> {{ collectPlan.contract_name }}</div>
        <div>第{{ collectPlan.installment_no }}期 {{ collectPlan.description }} —
          计划 <strong>{{ Number(collectPlan.plan_amount).toLocaleString() }}</strong> 元，
          已收 <span style="color:#67c23a">{{ Number(collectPlan.received_amount).toLocaleString() }}</span> 元
        </div>
      </div>
      <el-form label-width="80px">
        <el-form-item label="收款金额">
          <el-input-number v-model="collectForm.received_amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="收款日期">
          <el-date-picker v-model="collectForm.received_date" type="date" value-format="YYYY-MM-DD"
            style="width:100%" />
        </el-form-item>
        <el-form-item label="付款方式">
          <el-select v-model="collectForm.payment_method" style="width:100%">
            <el-option v-for="m in paymentMethodOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="银行流水号">
          <el-input v-model="collectForm.bank_reference" placeholder="选填" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="collectForm.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="collectVisible = false">取消</el-button>
        <el-button type="primary" :loading="collectSaving" @click="handleCollect">确认登记</el-button>
      </template>
    </el-dialog>
  </div>
</template>
