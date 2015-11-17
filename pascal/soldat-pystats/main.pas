const pystats_host = 'http://10.0.0.21:5000/';
const pystats_server = 'dm';
const pystats_secret = 'sdf123asd';

procedure OnPlayerKill(Killer, Victim: byte; Weapon: string);
var url: String;
begin
  url := pystats_host + pystats_server + '/script/submit_kill' 
    + '?secret='    + HTTPEncode(pystats_secret) 
    + '&map='       + HTTPEncode(CurrentMap)
    + '&weapon='    + HTTPEncode(Weapon)
    + '&killer='    + HTTPEncode(GetPlayerStat(Killer, 'Name'))
    + '&victim='    + HTTPEncode(GetPlayerStat(Victim, 'Name'))
    + '&timestamp=' + HTTPEncode(inttostr(DateTimeToUnix(now)));

  GetURL(url);
end;

procedure OnPlayerSpeak(ID: Byte; Text: String);
var url, body, rank, kills, since: String;
begin
  if Text = '!stats' then
  begin
    url := pystats_host + pystats_server + '/script/player_info?player=' + HTTPEncode(GetPlayerStat(ID, 'Name'));
    body := GetURL(url);

    if body = 'not found' then
    begin
      SayToPlayer(ID, 'You are not in our stats yet. Wait a bit.');
    end
    else
    begin
      rank := GetPiece(body, '|', 0);
      kills := GetPiece(body, '|', 1);
      since := GetPiece(body, '|', 2);
      SayToPlayer(ID, 'You''re #'+rank+' with '+kills+' kills since '+since+'!');
    end;
  end;
end;
