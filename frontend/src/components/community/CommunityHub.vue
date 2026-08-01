<template>
  <section class="community-hub page-section content-page">
    <header class="community-hero"><div><p class="section-kicker">CEBIAO COMMUNITY</p><h1>投标学院与 AI 投标社区</h1><p>学习招投标方法、理解行业机会，与同行分享项目经验和投标技巧。</p></div><div><strong>{{ articles.length }}</strong><span>学院内容</span><strong>{{ posts.length }}</strong><span>社区讨论</span></div></header>
    <nav class="community-tabs"><button :class="{active:tab==='academy'}" @click="tab='academy'">投标学院</button><button :class="{active:tab==='forum'}" @click="tab='forum'">AI 投标论坛</button></nav>
    <div v-if="tab==='academy'" class="academy-layout"><aside><strong>内容分类</strong><button :class="{active:category===''}" @click="category=''">全部内容</button><button v-for="item in categories" :key="item" :class="{active:category===item}" @click="category=item">{{ item }}</button></aside><main><article v-for="item in filteredArticles" :key="item.id"><div><span>{{ item.category }}</span><b v-if="item.is_featured">推荐</b></div><h2>{{ item.title }}</h2><p>{{ item.summary }}</p><footer><BookOpenIcon/>约 {{ item.read_minutes }} 分钟阅读 <ArrowRightIcon/></footer></article></main></div>
    <div v-else class="forum-layout"><main><article v-for="item in posts" :key="item.id"><div class="forum-avatar">{{ item.author_name.slice(0,1) }}</div><div><span>{{ item.category }} <b v-if="item.is_featured">精华</b></span><h2>{{ item.title }}</h2><p>{{ item.content }}</p><footer><strong>{{ item.author_name }}</strong><span><EyeIcon/>{{ item.view_count }}</span><span><ChatBubbleLeftRightIcon/>{{ item.reply_count }}</span></footer></div></article></main><aside><h2>分享你的投标经验</h2><p>{{ authenticated?'发布后将进入社区内容流。':'登录企业账号后可以参与交流。' }}</p><form v-if="authenticated" @submit.prevent="publishPost"><select v-model="form.category"><option>项目经验</option><option>投标技巧</option><option>行业机会</option><option>AI投标</option></select><input v-model.trim="form.title" placeholder="帖子标题"/><textarea v-model.trim="form.content" rows="5" placeholder="分享你的经验、问题或行业观察"></textarea><button class="button-primary" :disabled="publishing">{{ publishing?'发布中':'发布帖子' }}</button><span v-if="message">{{ message }}</span></form><a v-else class="button-primary" href="/">登录后参与交流</a></aside></div>
  </section>
</template>
<script setup>
import { ArrowRightIcon,BookOpenIcon,ChatBubbleLeftRightIcon,EyeIcon } from '@heroicons/vue/24/outline'
import { computed,onMounted,reactive,ref } from 'vue'
const props=defineProps({authenticated:{type:Boolean,default:false},csrfToken:{type:String,default:''}})
const tab=ref('academy'),articles=ref([]),posts=ref([]),categories=ref([]),category=ref(''),publishing=ref(false),message=ref('');const form=reactive({category:'项目经验',title:'',content:''})
const filteredArticles=computed(()=>category.value?articles.value.filter(item=>item.category===category.value):articles.value)
async function load(){const [a,p]=await Promise.all([fetch('/api/community/articles/'),fetch('/api/community/posts/')]);const ad=await a.json(),pd=await p.json();if(ad.ok){articles.value=ad.articles;categories.value=ad.categories}if(pd.ok)posts.value=pd.posts}
async function publishPost(){publishing.value=true;message.value='';try{const r=await fetch('/api/community/posts/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':props.csrfToken},body:JSON.stringify(form)});const p=await r.json();if(!r.ok||!p.ok)throw new Error(p.error||'发布失败');posts.value.unshift(p.post);form.title='';form.content='';message.value='发布成功'}catch(e){message.value=e.message}finally{publishing.value=false}}
onMounted(load)
</script>
