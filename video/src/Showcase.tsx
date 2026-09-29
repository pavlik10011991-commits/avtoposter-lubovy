import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Audio} from 'remotion';

const fonts = `
@font-face{font-family:Oswald;font-weight:700;src:url(${staticFile('oswald-latin-700-normal.woff2')})}
@font-face{font-family:Oswald;font-weight:700;src:url(${staticFile('oswald-cyrillic-700-normal.woff2')});unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:Montserrat;font-weight:700;src:url(${staticFile('montserrat-latin-700-normal.woff2')})}
@font-face{font-family:Montserrat;font-weight:700;src:url(${staticFile('montserrat-cyrillic-700-normal.woff2')});unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:'PT Serif';font-style:italic;src:url(${staticFile('pt-serif-latin-400-italic.woff2')})}
@font-face{font-family:'PT Serif';font-style:italic;src:url(${staticFile('pt-serif-cyrillic-400-italic.woff2')});unicode-range:U+0400-04FF,U+2116}`;
const CREAM = '#F4ECDF', GOLD = '#E6C9A0';

// mode: 'card' — клип во всю ширину на размытом фоне; 'full' — вертикальный кроп на весь экран
export type Shot = {src: string; from: number; dur: number; mode?: 'card' | 'full'; focus?: [number, number]; zoom?: [number, number];
  title: string; sub?: string; tag?: string; rate?: number};
export const showDefaults = {
  handle: '@lubov_pr_',
  voice: '',
  shots: [] as Shot[],
  endTitle: 'Сделаю такой же вам',
  endSub: 'бесплатно покажу за 15 минут, что ИИ сделает в вашем бизнесе',
  cta: 'ПИШИТЕ В ДИРЕКТ',
  endPhoto: 'lubov_01.jpg',
  endDur: 3.5,
};
export const showDuration = (p: typeof showDefaults, fps = 30) => Math.round((p.shots.reduce((a, s) => a + s.dur, 0) + p.endDur) * fps);

const Clip: React.FC<{s: Shot; n: number; blur?: boolean}> = ({s, n, blur}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const [z0, z1] = s.zoom ?? [1.0, 1.08];
  const z = interpolate(f, [0, n], [z0, z1]);
  const [fx, fy] = s.focus ?? [0.5, 0.5];
  const v = <OffthreadVideo src={staticFile(s.src)} startFrom={Math.round(s.from * fps)} playbackRate={s.rate ?? 1} muted
    style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: `${fx * 100}% ${fy * 100}%`,
      transform: `scale(${blur ? 1.3 : z})`, transformOrigin: `${fx * 100}% ${fy * 100}%`, filter: blur ? 'blur(38px) brightness(.42) saturate(1.3)' : undefined}} />;
  return v;
};

const Title: React.FC<{text: string; start: number}> = ({text, start}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const words = text.split(' ');
  return (<div style={{fontFamily: 'Oswald', fontWeight: 700, fontSize: 112, lineHeight: 1.0, textTransform: 'uppercase', textAlign: 'center', textShadow: '0 6px 30px rgba(0,0,0,.6)'}}>
    {words.map((w, i) => { const k = spring({frame: f - start - i * 3, fps, config: {damping: 14, stiffness: 180}});
      return <span key={i} style={{display: 'inline-block', margin: '0 12px', opacity: Math.min(1, k * 1.5), transform: `translateY(${(1 - k) * 50}px) scale(${0.8 + 0.2 * k})`}}>{w}</span>; })}
  </div>);
};

const ShotView: React.FC<{s: Shot; n: number}> = ({s, n}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const inK = spring({frame: f, fps, config: {damping: 200}, durationInFrames: 8});
  const flash = interpolate(f, [0, 4], [0.55, 0], {extrapolateRight: 'clamp'});
  const subK = spring({frame: f - 8, fps, config: {damping: 200}});
  return (
    <AbsoluteFill>
      {s.mode === 'full' ? (
        <AbsoluteFill style={{transform: `scale(${1.06 - 0.06 * inK})`}}><Clip s={s} n={n} /></AbsoluteFill>
      ) : (<>
        <AbsoluteFill><Clip s={s} n={n} blur /></AbsoluteFill>
        <div style={{position: 'absolute', left: 0, right: 0, top: 610, height: 700, overflow: 'hidden', boxShadow: '0 40px 90px rgba(0,0,0,.7)',
          transform: `scale(${0.94 + 0.06 * inK})`}}>
          <Clip s={s} n={n} />
        </div>
      </>)}
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 62%, rgba(0,0,0,.75) 100%)'}} />
      <div style={{position: 'absolute', top: 230, left: 40, right: 40, color: CREAM}}>
        {s.tag && <div style={{textAlign: 'center', marginBottom: 18}}><span style={{display: 'inline-block', background: GOLD, color: '#1b1614', font: '700 32px Montserrat', letterSpacing: '.2em', padding: '10px 26px', borderRadius: 8}}>{s.tag}</span></div>}
        <Title text={s.title} start={2} />
      </div>
      {s.sub && <div style={{position: 'absolute', bottom: 300, left: 70, right: 70, textAlign: 'center', color: CREAM, font: "italic 400 54px/1.25 'PT Serif'",
        opacity: subK, transform: `translateY(${(1 - subK) * 20}px)`, textShadow: '0 4px 20px rgba(0,0,0,.8)'}}>{s.sub}</div>}
      <AbsoluteFill style={{background: '#fff', opacity: flash}} />
    </AbsoluteFill>
  );
};

const End: React.FC<{p: typeof showDefaults}> = ({p}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const k = spring({frame: f, fps, config: {damping: 200}}); const c = spring({frame: f - 12, fps, config: {damping: 12, stiffness: 160}});
  return (<AbsoluteFill style={{background: '#0d0b0a'}}>
    <Img src={staticFile(p.endPhoto)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '30% 30%', transform: `scale(${1.1 - 0.06 * k})`}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg,rgba(0,0,0,.2) 0%,rgba(0,0,0,0) 35%,rgba(0,0,0,.8) 62%,rgba(0,0,0,.95) 100%)'}} />
    <div style={{position: 'absolute', left: 50, right: 50, bottom: 330, color: CREAM, textAlign: 'center'}}>
      <Title text={p.endTitle} start={0} />
      <div style={{font: "italic 400 50px/1.3 'PT Serif'", marginTop: 28, opacity: k}}>{p.endSub}</div>
    </div>
    <div style={{position: 'absolute', bottom: 150, width: '100%', textAlign: 'center', transform: `scale(${c})`}}>
      <span style={{display: 'inline-block', padding: '28px 60px', borderRadius: 80, background: CREAM, color: '#1b1614', font: '700 44px Montserrat', letterSpacing: '.06em'}}>{p.cta}</span>
    </div>
  </AbsoluteFill>);
};

export const Showcase: React.FC<typeof showDefaults> = (p) => {
  const {fps, durationInFrames} = useVideoConfig(); const f = useCurrentFrame();
  let acc = 0; const seq = p.shots.map((s) => { const st = acc; const n = Math.round(s.dur * fps); acc += n; return {s, st, n}; });
  return (<AbsoluteFill style={{background: '#000'}}>
    <style>{fonts}</style>
    {p.voice && <Audio src={staticFile(p.voice)} />}
    {seq.map(({s, st, n}, i) => <Sequence key={i} from={st} durationInFrames={n}><ShotView s={s} n={n} /></Sequence>)}
    <Sequence from={acc}><End p={p} /></Sequence>
    <div style={{position: 'absolute', top: 130, width: '100%', textAlign: 'center', color: CREAM, font: '700 28px Montserrat', letterSpacing: '.14em', opacity: .85}}>{p.handle}</div>
    <div style={{position: 'absolute', top: 0, left: 0, height: 8, width: `${(f / durationInFrames) * 100}%`, background: GOLD}} />
  </AbsoluteFill>);
};
