### Flag 1 ###
On va commencer par une alayse du disque bootable os-image.bin dans ghidra, en précisant **x86 16-bits real mode**.

On peut changer l'adresse de départ pour pointer sur **0x7c00**, addresse à laquelle le BIOS donne la main pour charger le **Master Boot Record**

voici ce que l'on obtient :

                             //
                             // ram 
                             // ram:0000:7c00-ram:0000:9bff
                             //
             assume DF = 0x0  (Default)
       0000:7c00 88 16 6e 7d     MOV        byte ptr [0x7d6e],DL
       0000:7c04 bd 00 90        MOV        BP,0x9000
       0000:7c07 89 ec           MOV        SP,BP
       0000:7c09 e8 34 01        CALL       FUN_0000_7d40                                    undefined FUN_0000_7d40()
       0000:7c0c e8 02 01        CALL       FUN_0000_7d11                                    undefined FUN_0000_7d11()
                             LAB_0000_7c0f                                   XREF[1]:     0000:7c0f(j)  
       0000:7c0f eb fe           JMP        LAB_0000_7c0f



Il est fort probable que les premieres fonctions servent à déchiffrer le payload et le charger en mémoire pour être exécuter, on va suivre ce qu'il se passe dans la fonction en 0x7d11 :

                         **************************************************************
                         *                          FUNCTION                          *
                         **************************************************************
                         undefined FUN_0000_7d11()
         undefined         AL:1           <RETURN>
                         FUN_0000_7d11                                   XREF[1]:     0000:7c0c(c)  
    0000:7d11 fa              CLI
    0000:7d12 0f 01 16        LGDT       word ptr [0x7cf0]
             f0 7c
    0000:7d17 0f 20 c0        MOV        EAX,CR0
    0000:7d1a 66 83 c8 01     OR         EAX,0x1
    0000:7d1e 0f 22 c0        MOV        CR0,EAX
    0000:7d21 ea 26 7d        JMPF       s__0000_7d8e+24
             08 00
    0000:7d26 66 b8 10        MOV        EAX,0xd88e0010
             00 8e d8
    0000:7d2c 8e d0           MOV        SS,AX
    0000:7d2e 8e c0           MOV        ES,AX
    0000:7d30 8e e0           MOV        FS,AX
    0000:7d32 8e e8           MOV        GS,AX
    0000:7d34 bd 00 00        MOV        BP,0x0
    0000:7d37 ff 00           INC        word ptr [BX + SI]
    0000:7d39 89 ec           MOV        SP,BP
    0000:7d3b e8 0d 00        CALL       LAB_0000_7d49+2
    0000:7d3e 00 00           ADD        byte ptr [BX + SI],AL
                         **************************************************************
                         *                          FUNCTION                          *
                         **************************************************************
                         undefined __cdecl16near FUN_0000_7d40()
         undefined         AL:1           <RETURN>
                         FUN_0000_7d40                                   XREF[1]:     0000:7c09(c)  
    0000:7d40 bb 00 10        MOV        BX,0x1000
    0000:7d43 b6 32           MOV        DH,0x32
    0000:7d45 8a 16 6e 7d     MOV        DL,byte ptr [0x7d6e]
                         LAB_0000_7d49+2                                 XREF[0,1]:   0000:7d3b(c)  
    0000:7d49 e8 18 ff        CALL       FUN_0000_7c64                                    undefined FUN_0000_7c64()
    0000:7d4c c3              RET
    0000:7d4d 31 ff           XOR        DI,DI
    0000:7d4f b9 00 20        MOV        CX,0x2000
    0000:7d52 00 00           ADD        byte ptr [BX + SI],AL
                         LAB_0000_7d54                                   XREF[1]:     0000:7d63(j)  
    0000:7d54 83 e7 3f        AND        DI,0x3f
    0000:7d57 8d 05           LEA        AX,[DI]
    0000:7d59 00 30           ADD        byte ptr [BX + SI],DH
    0000:7d5b 00 00           ADD        byte ptr [BX + SI],AL
    0000:7d5d 29 c8           SUB        AX,CX
    0000:7d5f 66 31 38        XOR        dword ptr [BX + SI],EDI
    0000:7d62 47              INC        DI
    0000:7d63 e2 ef           LOOP       LAB_0000_7d54
    0000:7d65 eb 00           JMP        LAB_0000_7d67
                         LAB_0000_7d67                                   XREF[1]:     0000:7d65(j)  
    0000:7d67 e8 94 92        CALL       SUB_0000_0ffe
    0000:7d6a ff              ??         FFh
    0000:7d6b ff              ??         FFh
    0000:7d6c eb              ??         EBh
    0000:7d6d fe              ??         FEh
    0000:7d6e 00              ??         00h
    0000:7d6f 43 68 61        ds         "Chargement du noyau en memoire"
             72 67 65 
             6d 65 6e 


On lance qemu avac les mêmes paramètres que dans le fichier run.py, en rajoutant les options **-s** (qui va ouvrir un gdbserver tcp:1234) et **-S** (qui ne va pas démarrer le CPU au lancement):

    qemu-system-x86_64 -snapshot -s -S -display none -serial stdio -drive format=raw,readonly,index=0,if=floppy,file=os-image.bin -hdb flag_04.txt -cpu Westmere

On peut ensuite lancer notre débugueur, se connecter à la socket et breaker en **0x7d67**, qui à l'air d'être le dernier appel de notre MBR, donc sans doute la fin du boot loader et le début du boot réel. 

    (gdb) target remote :1234
    Remote debugging using :1234
    warning: No executable has been specified and target does not support
    determining executable automatically.  Try using the "file" command.
    0x000000000000fff0 in ?? ()
    (gdb) b *0x7d67
    Breakpoint 1 at 0x7d67
    (gdb) c
    Continuing.


    Breakpoint 1, 0x0000000000007d67 in ?? ()
    

on continue d'une instruction et on peut voir qu'on se retrouve en 0x1000. Ça peut valoir le coup de décompiler cette partie :-)

    (gdb) si
    (gdb) dump binary memory 0x1000.bin 0x1000 0x2fff
    
on va suivre le premier appel (0x154c) en activant le layout asm, ce qui est plus facile pour suivre :

    (gdb) layout asm
      >x0x154c  push   %rbp                                                                                                                              x
       x0x154d  mov    %esp,%ebp                                                                                                                         x
       x0x154f  sub    $0x8,%esp                                                                                                                         x
       x0x1552  callq  0x12e1                                                                                                                            x
       x0x1557  callq  0x135f                                                                                                                            x
       x0x155c  callq  0x1448                                                                                                                            x
       x0x1561  callq  0x13d1                                                                                                                            x
       x0x1566  callq  0x150f                                                                                                                            x
       x0x156b  jmp    0x1566            

donc on peut voir qu'on appelle plein de fonction et que finalement on se retrouve dans un boucle à la fin .

on va breaker sur chacune de ces adresses pour voir à quel "moment" ça correspond:

    (gdb) b *0x1552
    Breakpoint 2 at 0x1552
    (gdb) b *0x1557
    Breakpoint 3 at 0x1557
    (gdb) b *0x155c
    Breakpoint 4 at 0x155c
    (gdb) b *0x1561
    Breakpoint 5 at 0x1561
    (gdb) b *0x1566
    Breakpoint 6 at 0x1566

sur le premier breakpoint, il ne se passe rien sur la VM

sur le 2e non plus

sur le 3e, la VM s'est initialisée mais ne nous a pas encore donné la main :

    Démarrage en mode réel 16-chibi ....
    Atterrissage en mode protégé 32-chibi ..
    Chargement du noyau .....

en 0x14a5, on a un call 0x1029, arrêtons-nous dessus

    (gdb) b *0x1029
    (gdb) c

Effectivement, la VM nous donne alors la main pour entrer le code d'activation

mettons un truc bidon, parfait on break en 0x1029

en 0x1040 on a récupéré la longueur de notre chaîne dans eax

On execute ensuite l'algorithme suivant :

    for p in len(my_str):
        if p%3 == 0:
            cipher+=my_str[p]^0x42 rol p
        if p%3 == 1:
            cipher+=my_str[p]^my_str[p-1] ror p 
        if p%3 == 2:
            cipher+=my_str[p]^my_str[p-1] rol p 
            
on vient finalement comparer ça avec les données présentes en 0x2be0

le code qui permet de reverser cette partie :

    def ror(b,l):
        l=l%8
        if l==0:
            return b
        return int(bin(b)[2:].zfill(8)[-l:]+bin(b)[2:].zfill(8)[:8-l], 2)
        
    def rol(b,l):
        l=l%8
        if l==0:
            return b
        return int(bin(b)[2:].zfill(8)[l:]+bin(b)[2:].zfill(8)[:l],2)
    
    cipher='149C0D893553C82EC47095C0F21003314A3C89C9C24C0D882D03341305114CA6516E9427E26259314110D88A44E415422D809369A1AA8902A85E032843B81098534DB46345C404A832882489616990'
    plain=''
    for k in range(len(cipher)//2):
        c = cipher[k*2:k*2+2]
        if k%3 == 0:
            p=ror(int(c,16),k)^0x42
        if k%3 == 1:
            old=ord(plain[k-1])
            p=rol(int(c,16),k)^old
        if k%3 == 2:
            old=ord(plain[k-1])
            p=ror(int(c,16),old)^old
        plain+=chr(p)

    print(plain)

ce qui nous donne :

    $ python3 decipher.py
    Vous savez, moi je ne crois pas qu'il y ait de bon ou de mauvais mot de passe.
    

Nous voilà avec le premier flag :

    Démarrage en mode réel 16-chibi ....
    Atterrissage en mode protégé 32-chibi ..
    Chargement du noyau .....
    Initialisation de la procédure gerboise bleue ......
    Code d'activation ?
    > Vous savez, moi je ne crois pas qu'il y ait de bon ou de mauvais mot de passe.
    Code correct !
    Premier fanion: DGA{local_flag_01}

### Flag 2 ###

le break suivant se passe en 0x1561 avec le call 0x13d1

    x0x13d1  push   %rbp            
    x0x13d2  mov    %esp,%ebp       
    x0x13d4  sub    $0x10,%esp      
    x0x13d7  pushq  $0x32           
    x0x13d9  pushq  $0x279d         
    x0x13de  callq  0x1b85          
    x0x13e3  pop    %rdx            
    x0x13e4  pop    %rcx            
    x0x13e5  pushq  $0xc8           
    x0x13ea  pushq  $0x277d         
    x0x13ef  callq  0x1b85          
    x0x13f4  callq  0x1290          
    x0x13f9  add    $0x10,%esp      
    x0x13fc  rex.W je 0x1411        
    x0x13ff  sub    $0xc,%esp       
    x0x1402  pushq  $0x27c8         
    x0x1407  callq  0x133d          
    x0x140c  callq  0x12f7          
    x0x1411  push   %rax            
    x0x1412  push   %rax            
    x0x1413  pushq  $0x14           
    x0x1415  pushq  $0x27ec         
    x0x141a  callq  0x1b85          
    x0x141f  movl   $0x2822,(%rsp)  
    x0x1426  callq  0x1b58          
    x0x142b  movl   $0x2835,(%rsp)  
    x0x1432  callq  0x1b58          
    x0x1437  movl   $0x2848,(%rsp)  
    x0x143e  callq  0x1b58          
    x0x1443  add    $0x10,%esp      
    x0x1446  leaveq                 
    x0x1447  retq                   
    x0x1448  push   %rbp            
    x0x1449  mov    %esp,%ebp       
    x0x144b  push   %rsi            

   
On voit quelques push 0x2xxx alors voir ce qu'il y a derrière :

    (gdb) x/s 0x279d
    0x279d: "Verification de l'intégrité matérielle "
    (gdb) x/s 0x277d
    0x277d: "..\n"
    (gdb) x/s 0x27c8
    0x27c8: "Intégrité matérielle compromise\n"
    (gdb) x/s 0x27ec
    0x27ec: "Intégrité matérielle tamponné.\nDouble tamponné!\n"
    (gdb)

on a donc un test en 0x13fc qui nous indique indique qu'on passe si on vérfie le call 0x1290

    B+>x0x1290  xor    %eax,%eax                                                                                                                         x
       x0x1292  cpuid                                                                                                                                    x
       x0x1294  cmp    $0x42524142,%ebx                                                                                                                  x
       x0x129a  jne    0x12d7                                                                                                                            x
       x0x129c  cmp    $0x5255454c,%ecx                                                                                                                  x
       x0x12a2  jne    0x12d7                                                                                                                            x
       x0x12a4  cmp    $0x4c49554f,%edx                                                                                                                  x
       x0x12aa  jne    0x12d7                                                                                                                            x
       x0x12ac  xor    %eax,%eax                                                                                                                         x
       x0x12ae  rex cpuid                                                                                                                                x
       x0x12b1  cmp    $0x10673,%eax                                                                                                                     x
       x0x12b6  jne    0x12d7                                                                                                                            x
       x0x12b8  cmp    $0x800,%ebx                                                                                                                       x
       x0x12be  jne    0x12d7                                                                                                                            x
       x0x12c0  cmp    $0x82882000,%ecx                                                                                                                  x
       x0x12c6  jne    0x12d7                                                                                                                            x
       x0x12c8  cmp    $0x78be9fd,%edx                                                                                                                   x
       x0x12ce  jne    0x12d7                                                                                                                            x
       x0x12d0  mov    $0x1,%eax                                                                                                                         x
       x0x12d5  jmp    0x12dc                                                                                                                            x
       x0x12d7  mov    $0x0,%eax                                                                                                                         x
       x0x12dc  retq                  
       
Donc on vient lancer la commande [cpuid](https://en.wikipedia.org/wiki/CPUID) en 0x1292 avec eax=0

En l'occurence, par défaut avec le CPU de type Westmere défini pour lancer qemu, nous avons un cpuid = GenuineIntel.

En décodant dans l'ordre ebx, edx, ecx en little indian, nous retrouvons le type de CPU attendu : **BARBOUILLEUR**

en 0x12ae, on relance un cpuid mais cette fois ci avec eax=1, qui nous ramène les fonctions cpu supportées dans edx et ecx et le modèle précis dans eax.

Par défaut nous avons 0x206c1 ce qui correspond à un [Intel Xeon](https://www.cpu-world.com/cgi-bin/CPUID.pl?MANUF=&FAMILY=&MODEL=&SIGNATURE=132801&PART=&ACTION=Filter&STEPPING=)
Il nous faudrait 0x10673, qui hélas n'est pas sur le site précédent, mais les cpus avec une signature proche sont Intel Core 2 duo (10671) et Intel Core 2 Duo Mobile (10674). Allons voir quels type de CPU sont supportés par qemu :

    $ qemu-system-x86_64 -cpu help
    Available CPUs:
    x86              486
    x86   Broadwell-IBRS  Intel Core Processor (Broadwell, IBRS)
    x86 Broadwell-noTSX-IBRS  Intel Core Processor (Broadwell, no TSX, IBRS)
    x86  Broadwell-noTSX  Intel Core Processor (Broadwell, no TSX)
    x86        Broadwell  Intel Core Processor (Broadwell)
    x86 Cascadelake-Server  Intel Xeon Processor (Cascadelake)
    x86           Conroe  Intel Celeron_4x0 (Conroe/Merom Class Core 2)
    x86        EPYC-IBPB  AMD EPYC Processor (with IBPB)
    x86             EPYC  AMD EPYC Processor
    x86     Haswell-IBRS  Intel Core Processor (Haswell, IBRS)
    x86 Haswell-noTSX-IBRS  Intel Core Processor (Haswell, no TSX, IBRS)
    x86    Haswell-noTSX  Intel Core Processor (Haswell, no TSX)
    x86          Haswell  Intel Core Processor (Haswell)
    x86   Icelake-Client  Intel Core Processor (Icelake)
    x86   Icelake-Server  Intel Xeon Processor (Icelake)
    x86   IvyBridge-IBRS  Intel Xeon E3-12xx v2 (Ivy Bridge, IBRS)
    x86        IvyBridge  Intel Xeon E3-12xx v2 (Ivy Bridge)
    x86     Nehalem-IBRS  Intel Core i7 9xx (Nehalem Core i7, IBRS update)
    x86          Nehalem  Intel Core i7 9xx (Nehalem Class Core i7)
    x86       Opteron_G1  AMD Opteron 240 (Gen 1 Class Opteron)
    x86       Opteron_G2  AMD Opteron 22xx (Gen 2 Class Opteron)
    x86       Opteron_G3  AMD Opteron 23xx (Gen 3 Class Opteron)
    x86       Opteron_G4  AMD Opteron 62xx class CPU
    x86       Opteron_G5  AMD Opteron 63xx class CPU
    x86           Penryn  Intel Core 2 Duo P9xxx (Penryn Class Core 2)
    x86 SandyBridge-IBRS  Intel Xeon E312xx (Sandy Bridge, IBRS update)
    x86      SandyBridge  Intel Xeon E312xx (Sandy Bridge)
    x86 Skylake-Client-IBRS  Intel Core Processor (Skylake, IBRS)
    x86   Skylake-Client  Intel Core Processor (Skylake)
    x86 Skylake-Server-IBRS  Intel Xeon Processor (Skylake, IBRS)
    x86   Skylake-Server  Intel Xeon Processor (Skylake)
    x86    Westmere-IBRS  Westmere E56xx/L56xx/X56xx (IBRS update)
    x86         Westmere  Westmere E56xx/L56xx/X56xx (Nehalem-C)
    x86           athlon  QEMU Virtual CPU version 2.5+
    x86         core2duo  Intel(R) Core(TM)2 Duo CPU     T7700  @ 2.40GHz
    x86          coreduo  Genuine Intel(R) CPU           T2600  @ 2.16GHz
    x86            kvm32  Common 32-bit KVM processor
    x86            kvm64  Common KVM processor
    x86             n270  Intel(R) Atom(TM) CPU N270   @ 1.60GHz
    x86          pentium
    x86         pentium2
    x86         pentium3
    x86           phenom  AMD Phenom(tm) 9550 Quad-Core Processor
    x86           qemu32  QEMU Virtual CPU version 2.5+
    x86           qemu64  QEMU Virtual CPU version 2.5+
    x86             base  base CPU model type with no features enabled
    x86             host  KVM processor with all supported host features (only available in KVM mode)
    x86              max  Enables all features supported by the accelerator in the current host

    Recognized CPUID flags:
      fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 pn clflush ds acpi mmx fxsr sse sse2 ss ht tm ia64 pbe
      pni pclmulqdq dtes64 monitor ds-cpl vmx smx est tm2 ssse3 cid fma cx16 xtpr pdcm pcid dca sse4.1 sse4.2 x2apic movbe popcnt tsc-deadline aes xsave osxsave avx f16c rdrand hypervisor
      fsgsbase tsc-adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx avx512f avx512dq rdseed adx smap avx512ifma pcommit clflushopt clwb avx512pf avx512er avx512cd sha-ni avx512bw avx512vl
      avx512vbmi umip pku ospke avx512vbmi2 gfni vaes vpclmulqdq avx512vnni avx512bitalg avx512-vpopcntdq la57 rdpid
      avx512-4vnniw avx512-4fmaps md-clear spec-ctrl arch-capabilities ssbd
      syscall nx mmxext fxsr-opt pdpe1gb rdtscp lm 3dnowext 3dnow
      lahf-lm cmp-legacy svm extapic cr8legacy abm sse4a misalignsse 3dnowprefetch osvw ibs xop skinit wdt lwp fma4 tce nodeid-msr tbm topoext perfctr-core perfctr-nb
      invtsc
      wbnoinvd ibpb amd-ssbd virt-ssbd amd-no-ssb
      xstore xstore-en xcrypt xcrypt-en ace2 ace2-en phe phe-en pmm pmm-en
      kvmclock kvm-nopiodelay kvm-mmu kvmclock kvm-asyncpf kvm-steal-time kvm-pv-eoi kvm-pv-unhalt kvm-pv-tlb-flush kvmclock-stable-bit

On retrouve 2 types de proc procher du Core 2 Duo :
* x86           Penryn  Intel Core 2 Duo P9xxx (Penryn Class Core 2)
* x86         core2duo  Intel(R) Core(TM)2 Duo CPU     T7700  @ 2.40GHz

En essayant le premier, c'est le bon ^^

Concernant les flags, il semble que ebx soit tout le temps égal à 0x800 donc pas de problème


ecx = 0x82882000 => 1000 0010 1000 1000 0010 0000 0000 0000 => bit13=cx16, bit19=sse4.1, bit23=popcnt, bit25=aes, bit31=hypervisor
par défaut, les bits 13, 19 et 31 sont déjà à 1, par contre on a aussi les bits 0 (sse3), 1 (pclmulqdq), 9 (ssse3) qu'il faudra passer à 0

edx = 0x78be9fd => 0111 1000 1011 1110 1001 1111 1101
par rapport aux valeurs par défaut, il faut aussi retirer les bits 9 (apic) et 12 (mttr)

le CPU à configurer pour lancer est donc Penryn,vendor=BARBOUILLEUR,-sse3,-ssse3,-pclmulqdq,popcnt,aes,-apic,-mtrr
On relance qemu avec ces paramètres :

    $ qemu-system-x86_64 -s -S -snapshot -drive format=raw,readonly,index=0,if=floppy,file=os-image.bin -hdb flag_04.txt -cpu Penryn,vendor=BARBOUILLEUR,-sse3,-ssse3,-pclmulqdq,popcnt,aes,-apic,-mtrr -display none -serial stdio
    Démarrage en mode réel 16-chibi ....
    Atterrissage en mode protégé 32-chibi ..
    Chargement du noyau .....
    Initialisation de la procédure gerboise bleue ......
    Code d'activation ?
    > Vous savez, moi je ne crois pas qu'il y ait de bon ou de mauvais mot de passe.
    Code correct !
    Premier fanion: DGA{local_flag_01}
    Verification de l'intégrité matérielle ..
    Intégrité matérielle tamponné.
    Double tamponné!
    Deuxième fanion: DGA{local_flag_02}
    Entrez le programme de guidage:
    >

ce qui nous donne le deuxième flag

### Flag 3 ###

Au démarrage, nous avons donc eu les appels suivants : 

    x0x154c  push   %rbp      
    x0x154d  mov    %esp,%ebp 
    x0x154f  sub    $0x8,%esp 
    x0x1552  callq  0x12e1    
    x0x1557  callq  0x135f    
    x0x155c  callq  0x1448   ; Flag 1 
    x0x1561  callq  0x13d1   ; Flag 2
    x0x1566  callq  0x150f    
    x0x156b  jmp    0x1566    
    
Il est fort probable que le flag 3 nous soit fourni par l'appel suivant en 0x150f !

    B+>x0x150f  push   %rbp                
       x0x1510  mov    %esp,%ebp           
       x0x1512  push   %rbx                
       x0x1513  lea    -0x408(%rbp),%ebx   
       x0x1519  sub    $0x410,%esp         
       x0x151f  pushq  $0x28e7             
       x0x1524  callq  0x1b58              
       x0x1529  movl   $0x2896,(%rsp)      
       x0x1530  callq  0x1b58              
       x0x1535  pop    %rax                
       x0x1536  pop    %rdx                
       x0x1537  pushq  $0x400              
       x0x153c  push   %rbx                
       x0x153d  callq  0x1ce0              
       x0x1542  callq  *%rbx               
       x0x1544  mov    -0x4(%rbp),%ebx     
       x0x1547  add    $0x10,%esp          
       x0x154a  leaveq                     
       x0x154b  retq                       
       x0x154c  push   %rbp                
       x0x154d  mov    %esp,%ebp         
   
en 0x1542, on a un call $rbx ! voilà qui est intéressant

On rajoute un breakpoint en 0x1542 et on rentre notre programme de guidage (abcdefgh en l'occurence pour moi)
   
    (gdb) b *0x1542
    Breakpoint 2 at 0x1542
    (gdb) c
    Continuing.

    Breakpoint 2, 0x0000000000001542 in ?? ()
    (gdb) i r $rbx
    rbx            0xfefbd8 16710616
    (gdb) x/s $rbx
    0xfefbd8:       "abcdefgh"

C'est bien ça, on vient directement exécuter nos opcodes. Mais lesquels ?

en regardant les strings qui sont définies à la fin, on recherche celles qui pourraient se rapporter au flag 3 :

    x/100s 0x2900
    ...
    0x29bd: "Bravo :)\n"
    0x29c7: "Voici la première partie du fanion N°3: \n"
    0x29f3: "DGA{local_"
    ...

On repasse en analyse sur ghidra pour retrouver à quel endroit 0x29bd est pushé :


                             LAB_0000_21a5                                   XREF[1]:     0000:217e(j)  
       0000:21a5 83 ec 0c        SUB        SP,0xc
       0000:21a8 68 bd 29        PUSH       0x29bd
       0000:21ab 00 00           ADD        byte ptr [BX + SI],AL
       0000:21ad e8 a6 f9        CALL       FUN_0000_1b56                                    undefined FUN_0000_1b56()

nous y arrivons depuis un call 0x2170, qui lui-même est effectué depuis une fonction en 0x10b0.

Si on revient sur les premiers call effectué par l'OS, en particulier le tout premier call 0x12e1, il s'agit d'initialiser la nouvelle table d'interruption :

Pour toutes les valeurs d'interruption < 0x20, on appelle 0x10b0 (en fait 0x2170, tiens ?) et au-dessus, on appelle 0x10d7, en fait 0x223d

en 0x217b  on a `cmp    $0x10,%eax`, si l' interruption demandée == 16 alors on afficher le début du troisième flag

en 0x2194  on a `cmp    $0x16,%eax`, si l'interruption == 22 alors on jump en 0x156d, sinon on affiche les messages suivants :

    x00    Interruption reçue : Division par zéro - halt
    x01    Déverminage
    x02    Déverminage
    x03    Déverminage
    x04    Interruption reçue : Dans un débordement détecté - halt
    x05    Interruption reçue : Hors limites - halt
    x06    Interruption reçue : Code d'opération invalide - halt 
    x07    Interruption reçue : Pas de coprocesseur - halt
    x08    Interruption reçue : Double Faute - halt
    x09    Interruption reçue : Dépassement de segment de coprocesseur - halt
    x0a    Interruption reçue : Mauvais segment d'état de tâche - halt
    x0b    Interruption reçue : Segment non présent - halt
    x0c    Interruption reçue : Défaut de pile - halt
    x0d    Interruption reçue : Défaut de protection générale - halt
    x0e    Interruption reçue : Défaut de page - halt
    x0f    Interruption reçue : Interruption inconnue - halt
    x11    Interruption reçue : Contrôle de l'alignement - halt
    x12    Interruption reçue : Contrôle de la machine - halt
    x13    Interruption reçue : Erreur arithmétique fatale - halt
    x14    Interruption reçue : Réservé - halt
    x15    Interruption reçue : Réservé - halt
    x17    Interruption reçue : Réservé - halt
    x18    Interruption reçue : Réservé - halt
    x19    Interruption reçue : Réservé - halt
    x1a    Interruption reçue : Réservé - halt
    x1b    Interruption reçue : Réservé - halt
    x1c    Interruption reçue : Réservé - halt
    x1d    Interruption reçue : Réservé - halt
    x1e    Interruption reçue : Réservé - halt
    x1f    Interruption reçue : Réservé - halt

       
Pour les tests, on va breaker en 0x1542 et remplir à la main l'espace mémoire qui nous intéresse :

je vais aussi breaker en 0x156d pour voir ce qu'il faut mettre pour avoir la deuxième partie du flag 3>

    (gdb) b *0x1542
    Breakpoint 1 at 0x1542
    (gdb) c
    Continuing.

    Breakpoint 1, 0x0000000000001542 in ?? ()
    (gdb) set {int}0xfefbd8=0x16cd10cd
    (gdb) b *0x156d
    Breakpoint 2 at 0x156d
    (gdb) c
    Continuing.

    Breakpoint 2, 0x000000000000156d in ?? ()


à ce moment j'ai bien obtenu la première partie du flag 3 avec l'interruption 10h :

    $ qemu-system-x86_64 -s -S -snapshot -drive format=raw,readonly,index=0,if=floppy,file=os-image.bin -hdb flag_04.txt -cpu Penryn,vendor=BARBOUILLEUR,-sse3,-ssse3,-pclmulqdq,popcnt,aes,-apic,-mtrr -display none -serial stdio
    Démarrage en mode réel 16-chibi ....
    Atterrissage en mode protégé 32-chibi ..
    Chargement du noyau .....
    Initialisation de la procédure gerboise bleue ......
    Code d'activation ?
    > Vous savez, moi je ne crois pas qu'il y ait de bon ou de mauvais mot de passe.
    Code correct !
    Premier fanion: DGA{local_flag_01}
    Verification de l'intégrité matérielle ..
    Intégrité matérielle tamponné.
    Double tamponné!
    Deuxième fanion: DGA{local_flag_02}
    Entrez le programme de guidage:
    > xxxx
    Bravo :)
    Voici la première partie du fanion N°3:
    DGA{local_


en 0x1576 j'ai mon premier test: `cmpl   $0x2a,0x20(%rax)` => il s'agit de la longueur de chaîne qui doit être égal à 0x2a (42 octets, y compris le retour chariot final)

en 0x157c j'ai mon deuxième test:  `cmpl   $0x1337,0x4(%rax)` => il s'agit de mettre 0x1337 à l'emplacement mémoire 0xfefb90

ça tombe bien, en 0x10b0 je fais un pushA et c'est $rdi qui vient se coller en 0xfefb90. Si je fait un push 0x1337 et un pop rdi dans mon shell code, je devrais récupérer la valeur attendue :

toujours à la main en breakant à 0x1542:

    set {int}0xfefbd8=0x00133768
    set {int}0xfefbdc=0x90905f00
    set {int}0xfefbe0=0x90909090
    set {int}0xfefbe4=0x90909090
    set {int}0xfefbe8=0x90909090
    set {int}0xfefbec=0x90909090
    set {int}0xfefbf0=0x90909090
    set {int}0xfefbf4=0x90909090
    set {int}0xfefbf8=0x90909090
    set {int}0xfefbfc=0xcd9010cd
    set {int}0xfefc00=0x16


Ça passe pour le flag3 :

    $ qemu-system-x86_64 -s -S -snapshot -drive format=raw,readonly,index=0,if=floppy,file=os-image.bin -hdb flag_04.txt -cpu Penryn,vendor=BARBOUILLEUR,-sse3,-ssse3,-pclmulqdq,popcnt,aes,-apic,-mtrr -display none -serial stdio
    Démarrage en mode réel 16-chibi ....
    Atterrissage en mode protégé 32-chibi ..
    Chargement du noyau .....
    Initialisation de la procédure gerboise bleue ......
    Code d'activation ?
    > Vous savez, moi je ne crois pas qu'il y ait de bon ou de mauvais mot de passe.
    Code correct !
    Premier fanion: DGA{local_flag_01}
    Verification de l'intégrité matérielle ..
    Intégrité matérielle tamponné.
    Double tamponné!
    Deuxième fanion: DGA{local_flag_02}
    Entrez le programme de guidage:
    > xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    Bravo :)
    Voici la première partie du fanion N°3:
    DGA{local_
    Bravo :)
    Voici la deuxième partie du fanion N°3:
    flag_03}
    Interruption reçue : Code d'opération invalide

Maintenant pour l'exploit en vrai, je suis passé par un script python afin d'injecter mes opcodes, ce qui a donné :

    $ python3 solve.py
    == proof-of-work: enabled ==
    please solve a pow first
    You can run the solver with:
        python3 <(curl -sSL https://goo.gle/kctf-pow) solve s.AHpp.MDznIinKcrRR9Ut9poH5
    ===================

    Solution? s.AHpp.MDznIinKcrRR9Ut9poH5
    s.AABG9yWheFABLbsmxuQil5Dc2gHuVHo6ds+CupHFqSpDqIXmD36lVswtzvjC8QGMoOD8RyjVNeXwMCdmykoMeKzqXlkXSPpLbfk2FkRrOdaLbeBwQl/nwVgvaIjTzJWx5QKh/1MZ7KH1PO09RJE7oSQLdgvuB8TkqwMBPAwzU8DhS8ArKND2irDmSYlLc9srQ67MHCiJ7Gj4M+86d1GwKkFU

    Correct
                ___    ____            ____                   _   _ _____
               / _ \  / ___|          / ___|         __   __ / | / |___  |
              | | | | \___ \   _____  \___ \         \ \ / / | | | |  / /
              | |_| |  ___) | |_____|  ___) |         \ V /  | |_| | / /
               \___/  |____/          |____/           \_/   |_(_)_|/_/

    Voulez-vous utiliser une configuration personnalisée pour le processeur ? [O/N] : Configuration cpu: Démarrage en mode réel 16-chibi ....
    Atterrissage en mode protégé 32-chibi ..
    Chargement du noyau .....
    Initialisation de la procédure gerboise bleue ......
    Code d'activation ?
    > message sent
    Vous savez, moi je ne crois pas qu'il y ait de bon ou de mauvais mot de passe.
    Code correct !
    Premier fanion: DGA{R0tat1on_d3_ch1bis}
    Verification de l'intégrité matérielle ..
    Intégrité matérielle tamponné.
    Double tamponné!
    Deuxième fanion: DGA{qemu_c_3st_qu4nd_m3m3_p4s_mal}
    Entrez le programme de guidage:
    > Donnees guidage envoyées
    Bravo :)
    Voici la premire partie du fanion N3:
    DGA{L3s_1nt3rupt1ons_
    Bravo :)
    Voici la deuxime partie du fanion N3:
    c_3st_c00l}
    Interruption reue : Code d'opration invalide
    end

Donc les 3 premiers flags :

**DGA{R0tat1on_d3_ch1bis}**

**DGA{qemu_c_3st_qu4nd_m3m3_p4s_mal}**

**DGA{L3s_1nt3rupt1ons_c_3st_c00l}**


### Flag 4 ###
Pour le flag 4 je ne sais pas. Une option serait de revenir en mode-réel pour restaurer les interruption du BIOS et donc accéder au fichier. Sinon il y a aussi les interruptions 20h et 21h qui semblent faire des choses sympas mais je n'ai pas pu determiner quoi exactement, ni surtout comment les exploiter.

l'interruption 20h execute le code en 0x22cc et l'interruption 21h le code en 0x15c5

0x22cc n'a pas l'air de faire grand chose à par incrémenter un compteur

0x15c5 semble venir récupérer les scan code des touches clavier pour les mapper avec un caractère 



