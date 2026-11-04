import {useRef,useState} from 'react';
import {Plus,FolderOpen,CaretRight,Export,UploadSimple,MagnifyingGlass} from '@phosphor-icons/react';
import type {Locale,Project} from './types';
import type {useProjects} from './useProjects';
import {isProject} from './state';
import {translator} from './i18n';

export function ProjectsPanel({projects,locale,openStudio,exportProject}:{projects:ReturnType<typeof useProjects>;locale:Locale;openStudio:()=>void;exportProject:()=>void}) {
  const t=translator(locale),input=useRef<HTMLInputElement>(null);
  const [error,setError]=useState(''),[query,setQuery]=useState('');
  const run=async(action:()=>Promise<void>)=>{setError('');try{await action();openStudio();}catch(cause){setError(cause instanceof Error && cause.message!=='Unsaved project'?cause.message:t('projectActionFailed'));}};
  const create=()=>run(()=>projects.create({title:t('newProject'),scenes:[{id:crypto.randomUUID(),title:t('newScene'),text:'',speechLanguage:'auto',emotion:'calm',temperature:.8,seed:'',audioIndex:null}]}));
  const importFile=async(file:File|undefined)=>{
    if(!file)return;
    try{
      if(file.size>10*1024*1024)throw new Error(t('invalidProjectFile'));
      const data:unknown=JSON.parse(await file.text());
      if(!isProject(data) || ('schemaVersion' in data && ![1,2].includes(data.schemaVersion as number)))throw new Error(t('invalidProjectFile'));
      const project:Project={title:data.title,scenes:data.scenes,...(data.mix?{mix:data.mix}:{})};await run(()=>projects.create(project));
    }catch{setError(t('invalidProjectFile'));}
    finally{if(input.current)input.current.value='';}
  };
  const sceneLabel=(count:number)=>locale==='ru'?(({one:'сцена',few:'сцены',many:'сцен',other:'сцены'} as Record<string,string>)[new Intl.PluralRules(locale).select(count)] ?? 'сцен'):(count===1?'scene':'scenes');
  const visible=projects.summaries.filter(p=>p.title.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  return <section className="projects-panel" aria-label={t('projects')}>
    <div className="projects-toolbar"><button type="button" className="primary" disabled={!projects.ready || projects.switching} onClick={()=>void create()}><Plus size={18} aria-hidden="true"/>{t('createProject')}</button><label className="file-upload-picker"><span className="quiet"><UploadSimple size={18} aria-hidden="true"/>{t('importProject')}</span><input ref={input} type="file" accept=".json,application/json" disabled={!projects.ready || projects.switching} aria-label={t('importProject')} onChange={event=>void importFile(event.target.files?.[0])}/></label><button type="button" className="quiet" onClick={exportProject}><Export size={18} aria-hidden="true"/>{t('exportProject')}</button></div>
    {error && <p className="generation-error" role="alert">{error}</p>}
    <label className="voice-search project-search" htmlFor="project-search"><span>{t('searchProjects')}</span><div><MagnifyingGlass size={18} aria-hidden="true"/><input id="project-search" type="search" value={query} maxLength={200} onChange={e=>setQuery(e.target.value)} placeholder={t('projectTitle')}/></div></label>
    <div className="project-table">{visible.map(item=><button type="button" className="project-table-row" key={item.id} disabled={projects.switching} onClick={()=>void run(()=>projects.open(item.id))}><FolderOpen size={28} aria-hidden="true"/><span><strong>{item.id===projects.id?projects.project.title || t('newProject'):item.title || t('newProject')}</strong><small>{item.sceneCount} {sceneLabel(item.sceneCount)}{item.id===projects.id?` / ${t('currentProject')}`:''}</small></span><span>{new Intl.DateTimeFormat(locale,{dateStyle:'medium',timeStyle:'short'}).format(new Date(item.updatedAt))}</span><CaretRight size={20} aria-hidden="true"/></button>)}</div>
    {!visible.length && <p className="empty-copy">{t(query?'noProjectsFound':'loadingProjects')}</p>}
  </section>;
}
