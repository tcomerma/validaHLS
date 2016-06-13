#!/usr/local/python-2.7/bin/python
#
# Utilitat per comprovar l'estat d'streams HLS i mostrar-ne les caracteristiques
#
# Toni Comerma
# juliol de 2014
#
# Aquest invent funciona gracies a la llibreria de tractament de playlists
# https://github.com/globocom/m3u8
#
# PD: Primer script en python que faig
#
# feb-2015: Modificat per incloure monitoritzacio de EXT-X-TARGETDURATION

import m3u8
import sys, getopt, urllib2, httplib, signal

def signal_handler(signal, frame):
        print('Cancelat per Ctrl+C!')
        sys.exit(0)

stats_text=''

# Analisi dels SubManfests (Playlists que contenen els .ts i que van variant)
def analitzaSubManifestNagios(m, test_ts,test_target_duration,expected_target_duration):
   err=''
   warn=''
   status=0
   global stats_text

   u=None
   try:
      if m.uri.startswith('http'):
         url = m.uri
      else:
         url = m.base_uri + "/" + m.uri
      u = m3u8.load(url)
   except urllib2.URLError, e:
      stats_text+=" ERR"
      status=2
   else:
      # Generar warning si versio 6 o posterior
      if m.stream_info.program_id and int(u.version) > 5:
          stats_text+=" WARN"
          status=1 
      if str(len (u.segments)) == 0:
          stats_text+=" ERR"
          status=2
      else:
         if test_ts:
             for s in u.segments:
                try:
                   url = m.base_uri + "/" + s.uri
                   h = urllib2.Request(url)
                   h.get_method = lambda : 'HEAD'
                   resp = urllib2.urlopen(h)
                   stats_text+=" OK"
                except:
                  status=2
                  stats_text+=" KO"
         if test_target_duration:
             if u.target_duration > int(expected_target_duration):
                if status < 2:
                   status = 1
                   stats_text+=" WARN (targetduration)"               
      if status == 0:
         stats_text+=" OK"
   return status 

# Analisi dels SubManfests (Playlists que contenen els .ts i que van variant)
def analitzaSubManifestSilent(m, test_ts):
   u=None

   try:
      if m.uri.startswith('http'):
         url = m.uri
      else:
         url = m.base_uri + "/" + m.uri    
      u = m3u8.load(url)
   except urllib2.HTTPError, e:
      print "  ERROR: Codi HTTP " + str(e.code) + ": " + url
   except urllib2.URLError, e:
      print "  ERROR: " + url
   else:
      if str(len (u.segments)) == 0:
          print "  ERROR: " + url
      else:
          if test_ts:
             print "  OK: " + url + " : ",
             for s in u.segments:
                try:
                   url = m.base_uri + "/" + s.uri
                   h = urllib2.Request(url)
                   h.get_method = lambda : 'HEAD'
                   resp = urllib2.urlopen(h)
                   print " OK",
                except:
                   print " KO",
             print " "
          else:
             print "  OK: " + url


# Analisi dels SubManfests (Playlists que contenen els .ts i que van variant)
def analitzaSubManifest(m,test_ts):
   u=None

   print "  URL base : " + m.base_uri
   print "  URL      : " + m.uri
   print "  Informacio (EXT-X-STREAM-INF)"
   print "     Program ID (PROGRAM-ID): " + str(m.stream_info.program_id) 
   if m.stream_info.program_id:
       print "                              (deprecated; no hauria d'estar present)"
   print "     Bandwidth (BANDWIDTH)  : " + m.stream_info.bandwidth
   print "     Codecs (CODECS)        : " + m.stream_info.codecs
   if m.stream_info.resolution:
      print "     Resolution (RESOLUTION): " + str(m.stream_info.resolution[0])+ "x" + str(m.stream_info.resolution[1])
   else:
      print "     Resolution (RESOLUTION): None"   
   print "  Contingut"
   try:
      if m.uri.startswith('http'):
         url = m.uri
      else:
         url = m.base_uri + "/" + m.uri
      u = m3u8.load(url)
   except urllib2.HTTPError, e:
      print "     ERROR: Codi HTTP " + str(e.code) + ": " + url      
   except urllib2.URLError, e:
      print "     ERROR: No s'ha pogut connectar"
   else:
      if str(len (u.segments)) == 0:
          print "     ERROR: playlist buida"
      else: 
          print "    Playlist complerta (EXT-X-ENDLIST): " + str (u.is_endlist)
          if u.is_endlist:
              print "     ATENCIO: Si es un HLS live, NO hauria d'apareixer"
          print "    Versio (EXT-X-VERSION):            " + str(u.version)
          print "    Permet cache (EXT-X-ALLOW-CACHE):  " + str(u.allow_cache) 
          print "    Durada objectiu playlist (EXT-X-TARGETDURATION): " + str(u.target_duration) 
          print "    Sequencia (EXT-X-MEDIA-SEQUENCE):  " + str(u.media_sequence)
          if test_ts:
             print "     Segments:                      :  " + str(len (u.segments)) + ": ",
             for s in u.segments:
                try:
                   url = m.base_uri + "/" + s.uri
                   h = urllib2.Request(url)
                   h.get_method = lambda : 'HEAD'
                   resp = urllib2.urlopen(h)
                   print " OK",
                except:
                   print " KO",
             print " "
          else:
             print "     Segments:                      :  " + str(len (u.segments)),

def analitzaManifest(m):
   u=None
   if str(len (m.segments)) == 0:
      print "     ERROR: playlist buida"
   else: 
      print "    Playlist complerta (EXT-X-ENDLIST): " + str (m.is_endlist)
      if m.is_endlist:
          print "     ATENCIO: Si es un HLS live, NO hauria d'apareixer"
      print "    Versio (EXT-X-VERSION):            " + str(m.version)
      print "    Permet cache (EXT-X-ALLOW-CACHE):  " + str(m.allow_cache) 
      print "    Durada objectiu playlist (EXT-X-TARGETDURATION): " + str(m.target_duration) 
      print "    Sequencia (EXT-X-MEDIA-SEQUENCE):  " + str(m.media_sequence)
      print "    Segments:                      :  " + str(len (m.segments))

def analitzaManifestSilent(m, url):
   if str(len (m.segments)) == 0:
      print "ERROR: playlist buida" + url 
   else: 
      print "OK: " + url

def analitzaManifestNagios(m, url):
   if str(len (m.segments)) == 0:
      print "ERROR: playlist buida" + url
      sys.exit(2) 
   else: 
      print "OK: " + url
      sys.exit(0) 


def us():
   print 'validaHLS.py [-h] [-n] [-s] [-t] -u <url>'
   print "  -u, --url      : URL a testejar. Unic parametre obligatori"
   print "  -h, --help     : Aquesta informacio"
   print "  -s, --silent   : Resultats mes concisos"
   print "  -n, --nagios   : Resultats compatibles amb un check de nagios"
   print "  -t, --test-ts  : Comprova el segments de la playlist. No els descarrega, nomes fa un HEAD"
   print "  -d <n>, --target-duration <n>  : Comprova que el valor de EXT-X-TARGET-DURATION estigui per sota de n. Nomes en mode Nagios"


def main(argv):
   url = ''
   silent = False
   nagios = False
   status = 0
   test_ts = False
   test_target_duration = False
   expected_target_duration = 0
   global stats_text

   try:
      opts, args = getopt.getopt(argv,"hsnu:td:",["url=", "help", "silent", "nagios","test-ts","target-duration="])
   except getopt.GetoptError:
      sys.exit(2)
   for opt, arg in opts:
      if opt in ("-h", "--help"):
         us()
         sys.exit()
      elif opt in ("-u", "--url"):
         url = arg
      elif opt in ("-s", "--silent"):
         silent = True
      elif opt in ("-n", "--nagios"):
         nagios = True
      elif opt in ("-t", "--test-ts"):
         test_ts = True
      elif opt in ("-d", "--target-duration"):
         test_target_duration = True
         expected_target_duration = arg
   # S'ha indicat URL
   if url == '':
      print 'ERROR: Cal indicar URL a testejar'
      us()
      sys.exit(2)

   # Llegim URL
   try:
      variant_m3u8 = m3u8.load(url)
   except urllib2.HTTPError, e:
      print "CRITICAL: Error HTTP " + str(e.code) + ": " + url
      sys.exit(2)   
   except urllib2.URLError, e:
      print "CRITICAL: No s'ha pogut connectar a " + url
      sys.exit(2)
   except:
      print "CRITICAL: Error desconegut al connectar a " + url
      sys.exit(2)


   
   # Analitzem
   # Si la playlist principal esta buida o corrupta, ja no continuem
   if not variant_m3u8.is_variant and (len(variant_m3u8.segments) == 0):
      print "CRITICAL: playlist buida o erronia: " + url
      sys.exit(2)


   if nagios:
      if variant_m3u8.is_variant:
          for playlist in variant_m3u8.playlists:
             status=max(status,analitzaSubManifestNagios(playlist, test_ts,test_target_duration,expected_target_duration))                 
      else:
         status=max(status,analitzaManifestNagios(variant_m3u8, url))

      # Resultats
      if status == 2:
          print "CRITICAL: (" + stats_text + ") " + url
          sys.exit(2)
      elif status == 1:        
          print "WARNING: (" + stats_text + ") " + url
          sys.exit(1)
      print "OK: (" + stats_text + ") " + url
      sys.exit(0)
   elif silent:
      if variant_m3u8.is_variant:
          print "OK: " + url
          for playlist in variant_m3u8.playlists:
             analitzaSubManifestSilent(playlist,test_ts)
      else:
          analitzaManifestSilent(variant_m3u8, url)
   else:
      print "Manifest principal"
      print "---------------------------------------------------------------"
      print "URL: " + url
      print "Variant (multiples bitrates): " + str(variant_m3u8.is_variant)
      if variant_m3u8.is_variant:
          print "Versio: " + str(variant_m3u8.version)
          for playlist in variant_m3u8.playlists:
             print "Sub Manifest"
             analitzaSubManifest(playlist,test_ts)
      else:
           analitzaManifest(variant_m3u8)

####################################################
# Crida al programa principal
if __name__ == "__main__":
   signal.signal(signal.SIGINT, signal_handler)
   main(sys.argv[1:])

