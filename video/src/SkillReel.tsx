import React from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Audio} from 'remotion';

const fonts = `
@font-face{font-family:Oswald;font-weight:700;src:url(${staticFile('oswald-latin-700-normal.woff2')})}
@font-face{font-family:Oswald;font-weight:700;src:url(${staticFile('oswald-cyrillic-700-normal.woff2')});unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:Montserrat;font-weight:700;src:url(${staticFile('montserrat-latin-700-normal.woff2')})}
@font-face{font-family:Montserrat;font-weight:700;src:url(${staticFile('montserrat-cyrillic-700-normal.woff2')});unicode-range:U+0400-04FF,U+2116}`;
const CREAM = '#F4ECDF', GOLD = '#E6C9A0';

export type Shot = {src: string; from: number; dur: number; rate?: number; title: string; sub: string; zoom?: [number, number, number]};
export const skillDefaults = {
  handle: '@lubov_pr_',
  topic: 'скил дизайна в Claude',
  voice: '' as string,
  shots: [
    {src: '3e97_0-20.mp4', from: 12.3, dur: 4, title: 'Этот сайт сделал Claude', sub: 'А дизайн ему поставил всего один скил', zoom: [0.62, 0.5, 1.12]},
    {src: '334e_295-335.mp4', from: 12.5, dur: 4, title: 'Шаг 1. Скил дизайна', sub: 'Скил — это навык. Как нанять дизайнера внутрь Claude', zoom: [0.3, 0.68, 1.8]},
    {src: '3e97_85-165.mp4', from: 21, dur: 3.5, title: 'Шаг 2. Одна команда', sub: 'Claude сам даёт команду установки…', zoom: [0.5, 0.35, 1.9]},
    {src: '3e97_85-165.mp4', from: 50, dur: 3.5, title: 'Шаг 2. Одна команда', sub: '…вставляете в терминал — и он ставится сам', zoom: [0.33, 0.3, 1.7]},
    {src: '334e_535-605.mp4', from: 8, dur: 5, title: 'Шаг 3. Пишем словами', sub: '«Хочу сайт на миллион долларов: тёмная премиум-сцена, свечение»', zoom: [0.33, 0.32, 1.9]},
    {src: '3e97_505-545.mp4', from: 19, dur: 4, title: 'Результат', sub: 'Раньше за такой сайт отдавали 100 тысяч', zoom: [0.5, 0.5, 1.1]},
    {src: '3e97_925-1010.mp4', from: 53.5, dur: 5, title: 'Сделаю такой же вам', sub: 'Поставлю скилы и соберу сайт за вас', zoom: [0.5, 0.5, 1.08]},
  ] as Shot[],
  cta: 'ПИШИТЕ В ДИРЕКТ',
};
export const skillDuration = (shots: Shot[], fps = 30) => Math.round(shots.reduce((a, s) => a + s.dur, 0) * fps);

const ShotView: React.FC<{s: Shot; frames: number}> = ({s, frames}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const [zx, zy, zs] = s.zoom ?? [0.5, 0.5, 1];
  const k = spring({frame: f, fps, config: {damping: 200}, durationInFrames: 18});
  const sc = 1 + (zs - 1) * k + 0.03 * (f / frames);
  const inOp = interpolate(f, [0, 6], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity: inOp}}>
      <div style={{width: '100%', height: '100%', transform: `scale(${sc})`, transformOrigin: `${zx * 100}% ${zy * 100}%`}}>
        <OffthreadVideo src={staticFile(s.src)} startFrom={Math.round(s.from * fps)} playbackRate={s.rate ?? 1} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </div>
    </AbsoluteFill>
  );
};

export const SkillReel: React.FC<typeof skillDefaults> = (p) => {
  const f = useCurrentFrame(); const {fps, durationInFrames} = useVideoConfig();
  let acc = 0; const seq = p.shots.map((s) => { const st = acc; acc += Math.round(s.dur * fps); return {s, st, n: Math.round(s.dur * fps)}; });
  const cur = seq.find((x) => f >= x.st && f < x.st + x.n) ?? seq[seq.length - 1];
  const pop = spring({frame: f - cur.st, fps, config: {damping: 200}});
  const ctaIn = spring({frame: f - (durationInFrames - 5 * fps), fps, config: {damping: 200}});
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 35%, #2a211c 0%, #0d0b0a 70%)', color: CREAM}}>
      <style>{fonts}</style>
      {p.voice && <Audio src={staticFile(p.voice)} />}
      <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center', font: '700 28px Montserrat', letterSpacing: '.12em', opacity: .8}}>{p.handle}</div>
      <div style={{position: 'absolute', top: 180, width: '100%', textAlign: 'center', font: '700 30px Montserrat', letterSpacing: '.3em', textTransform: 'uppercase', color: GOLD}}>{p.topic}</div>
      <div style={{position: 'absolute', top: 250, left: 50, right: 50, textAlign: 'center', fontFamily: 'Oswald', fontWeight: 700, fontSize: 96, lineHeight: 1.02, textTransform: 'uppercase', opacity: pop, transform: `translateY(${(1 - pop) * 30}px)`}}>{cur.s.title}</div>
      <div style={{position: 'absolute', top: 520, left: 20, right: 20, height: 700, borderRadius: 28, overflow: 'hidden', border: `3px solid ${GOLD}`, background: '#000', boxShadow: '0 30px 80px rgba(0,0,0,.6)'}}>
        {seq.map(({s, st, n}, i) => (
          <Sequence key={i} from={st} durationInFrames={n}><ShotView s={s} frames={n} /></Sequence>
        ))}
      </div>
      <div style={{position: 'absolute', top: 1290, left: 70, right: 70, textAlign: 'center', font: '700 50px/1.3 Montserrat', opacity: pop}}>
        <span style={{background: 'rgba(244,236,223,.12)', padding: '6px 14px', borderRadius: 12, boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone'}}>{cur.s.sub}</span>
      </div>
      <div style={{position: 'absolute', bottom: 150, width: '100%', textAlign: 'center', opacity: ctaIn, transform: `scale(${0.9 + 0.1 * ctaIn})`}}>
        <span style={{display: 'inline-block', padding: '26px 56px', borderRadius: 80, background: CREAM, color: '#1b1614', font: '700 40px Montserrat', letterSpacing: '.06em'}}>{p.cta}</span>
      </div>
    </AbsoluteFill>
  );
};
